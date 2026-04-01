"""
Serwis KSeF (Krajowy System e-Faktur) — integracja z API 2.0.

Zmiany względem API 1.0 (wyłączonego 2026-02-01):
  - Nowe URL-e: api.ksef.mf.gov.pl / api-test.ksef.mf.gov.pl
  - Autoryzacja: RSA-OAEP szyfrowanie tokenu (zamiast SHA-256)
  - Sesja: osobny proces (POST /sessions/online)
  - Faktury: szyfrowane AES-256-CBC przed wysyłką
  - Format XML: FA(3) (zamiast FA(2), obowiązkowy od 2026-02-01)

Wymagania:
    pip install cryptography

Konfiguracja (.env):
  KSEF_SANDBOX = True/False
  KSEF_NIP     = NIP firmy (10 cyfr)
  KSEF_TOKEN   = token serwisowy z panelu KSeF
"""
import base64
import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_der_x509_certificate, load_pem_x509_certificate
from django.conf import settings

logger = logging.getLogger('invoices.ksef')

UPO_MAX_RETRIES = 30
UPO_RETRY_DELAY = 3

# Namespace FA(3) — obowiązkowy od 2026-02-01
FA3_NS = 'http://crd.gov.pl/wzor/2025/06/25/13775/'


def _api_url(path: str) -> str:
    return f"{settings.KSEF_API_URL}{path}"


# ===========================================================================
# Klucz publiczny MF (RSA — do szyfrowania tokenu i klucza AES)
# ===========================================================================

_cached_public_key = None


def _get_mf_public_key():
    """
    Pobiera klucz publiczny MF z /security/public-key-certificates.
    Wynik jest cachowany na czas życia procesu.
    """
    global _cached_public_key
    if _cached_public_key:
        return _cached_public_key

    resp = requests.get(
        _api_url("/security/public-key-certificates"),
        headers={"Accept": "application/json"},
        timeout=15,
    )
    logger.debug("KSeF /security/public-key-certificates status=%d body=%s",
                 resp.status_code, resp.text[:500])
    resp.raise_for_status()

    certs = resp.json()
    cert_data = None

    # Szukaj certyfikatu do szyfrowania symetrycznego
    for cert in certs:
        usage = str(cert.get('usage', ''))
        if 'Symmetric' in usage or 'Encryption' in usage:
            cert_data = cert.get('certificate')
            logger.debug("KSeF: wybrany certyfikat usage=%s", usage)
            break
    if not cert_data and certs:
        cert_data = certs[0].get('certificate')
        logger.debug("KSeF: użyto pierwszego certyfikatu (fallback)")

    if not cert_data:
        raise ValueError("KSeF: brak certyfikatu publicznego w /security/public-key-certificates")

    # Certyfikat może być Base64-DER lub PEM
    try:
        cert_bytes = base64.b64decode(cert_data)
        cert = load_der_x509_certificate(cert_bytes)
    except Exception:
        cert = load_pem_x509_certificate(cert_data.encode())

    _cached_public_key = cert.public_key()
    return _cached_public_key


def _rsa_oaep_encrypt(data: bytes) -> str:
    """Szyfruje dane kluczem publicznym MF (RSA-OAEP/SHA-256/MGF1). Zwraca Base64."""
    public_key = _get_mf_public_key()
    encrypted = public_key.encrypt(
        data,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(encrypted).decode('ascii')


# ===========================================================================
# Autoryzacja tokenem serwisowym — 6 kroków
# ===========================================================================

def _get_access_token() -> str:
    """
    Autoryzuje się tokenem serwisowym KSeF API 2.0.
    Zwraca accessToken (JWT) do wszystkich operacji.

    Flow:
    1. POST /auth/challenge (bez body) → {challenge, timestampMs}
    2. RSA-OAEP("{token}|{timestampMs}") → encryptedToken
    3. POST /auth/ksef-token → {authenticationToken, referenceNumber}
    4. GET /auth/{referenceNumber} polling (status.code == 200)
    5. POST /auth/token/redeem → {accessToken, refreshToken}
    """
    nip   = settings.KSEF_NIP
    token = settings.KSEF_TOKEN

    if not nip or not token:
        raise ValueError("KSEF_NIP lub KSEF_TOKEN nie są skonfigurowane w .env")

    logger.info("KSeF: rozpoczynam autoryzację (sandbox=%s, NIP=%s)", settings.KSEF_SANDBOX, nip)

    # Krok 1: challenge
    challenge_resp = requests.post(
        _api_url("/auth/challenge"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=15,
    )
    logger.debug("KSeF /auth/challenge status=%d body=%s",
                 challenge_resp.status_code, challenge_resp.text[:500])
    try:
        challenge_resp.raise_for_status()
        challenge_data = challenge_resp.json()
    except Exception:
        logger.error("KSeF /auth/challenge — odpowiedź: %s", challenge_resp.text[:500])
        raise

    challenge    = challenge_data["challenge"]
    timestamp_ms = challenge_data["timestampMs"]

    # Krok 2: szyfrowanie tokenu
    plaintext = f"{token}|{timestamp_ms}".encode('utf-8')
    encrypted_token_b64 = _rsa_oaep_encrypt(plaintext)

    # Krok 3: ksef-token
    auth_resp = requests.post(
        _api_url("/auth/ksef-token"),
        json={
            "challenge":          challenge,
            "contextIdentifier":  {"type": "Nip", "value": nip},
            "encryptedToken":     encrypted_token_b64,
        },
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=15,
    )
    logger.debug("KSeF /auth/ksef-token status=%d body=%s",
                 auth_resp.status_code, auth_resp.text[:500])
    try:
        auth_resp.raise_for_status()
        auth_data = auth_resp.json()
    except Exception:
        logger.error("KSeF /auth/ksef-token — odpowiedź: %s", auth_resp.text[:500])
        raise

    authentication_token = auth_data["authenticationToken"]["token"]
    reference_number     = auth_data["referenceNumber"]

    # Krok 4: polling statusu autoryzacji
    for attempt in range(UPO_MAX_RETRIES):
        status_resp = requests.get(
            _api_url(f"/auth/{reference_number}"),
            headers={
                "Authorization": f"Bearer {authentication_token}",
                "Accept":        "application/json",
            },
            timeout=15,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()
        code = status_data.get("status", {}).get("code")
        logger.debug("KSeF auth polling (próba %d): status.code=%s", attempt + 1, code)

        if code == 200:
            break
        if code and code >= 400:
            desc = status_data.get("status", {}).get("description", "")
            raise RuntimeError(f"KSeF: autoryzacja nieudana (code={code}): {desc}")
        time.sleep(UPO_RETRY_DELAY)
    else:
        raise TimeoutError("KSeF: timeout autoryzacji — przekroczono limit prób")

    # Krok 5: redeem → accessToken
    redeem_resp = requests.post(
        _api_url("/auth/token/redeem"),
        headers={
            "Authorization": f"Bearer {authentication_token}",
            "Accept":        "application/json",
        },
        timeout=15,
    )
    logger.debug("KSeF /auth/token/redeem status=%d body=%s",
                 redeem_resp.status_code, redeem_resp.text[:300])
    redeem_resp.raise_for_status()
    access_token = redeem_resp.json()["accessToken"]["token"]
    logger.info("KSeF: uzyskano accessToken (...%s)", access_token[-12:])
    return access_token


def _close_auth_session(access_token: str) -> None:
    """Zamknij sesję autoryzacji po zakończeniu pracy."""
    try:
        requests.delete(
            _api_url("/auth/sessions/current"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept":        "application/json",
            },
            timeout=10,
        )
        logger.debug("KSeF: sesja autoryzacji zamknięta")
    except Exception as e:
        logger.warning("KSeF: nie udało się zamknąć sesji autoryzacji: %s", e)


# ===========================================================================
# Szyfrowanie AES-256-CBC (faktury)
# ===========================================================================

def _aes_encrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    """Szyfruje dane AES-256-CBC z PKCS#7 padding."""
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()


# ===========================================================================
# Generowanie XML FA(3)
# ===========================================================================

def _seller_data() -> dict:
    return settings.INVOICE_SELLER_DATA


def _build_fa3_xml(invoice, is_correction: bool = False) -> bytes:
    """
    Buduje minimalny poprawny XML FA(3) dla danej faktury.
    Zwraca zakodowany XML jako bytes (UTF-8).
    """
    seller = _seller_data()
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    ET.register_namespace('', FA3_NS)
    ns = FA3_NS

    def tag(name):
        return f'{{{ns}}}{name}'

    root = ET.Element(tag('Faktura'))
    root.set('xmlns', ns)

    # ── Nagłówek ─────────────────────────────────────────────────────────
    nagl = ET.SubElement(root, tag('Naglowek'))
    ET.SubElement(nagl, tag('KodFormularza'),
                  kodSystemowy="FA (3)", wersjaSchemy="1-0E").text = "FA"
    ET.SubElement(nagl, tag('WariantFormularza')).text = "3"
    ET.SubElement(nagl, tag('DataWytworzeniaFa')).text = now_str
    ET.SubElement(nagl, tag('SystemInfo')).text = "wyznaczresurs.pl v2.0"

    # ── Podmiot1 (sprzedawca) ─────────────────────────────────────────────
    p1 = ET.SubElement(root, tag('Podmiot1'))
    ds1 = ET.SubElement(p1, tag('DaneIdentyfikacyjne'))
    ET.SubElement(ds1, tag('NIP')).text = seller['nip']
    ET.SubElement(ds1, tag('PelnaNazwa')).text = seller['name']
    adres1 = ET.SubElement(p1, tag('Adres'))
    ET.SubElement(adres1, tag('AdresL1')).text = seller['address']

    # ── Podmiot2 (nabywca) ────────────────────────────────────────────────
    p2 = ET.SubElement(root, tag('Podmiot2'))
    ds2 = ET.SubElement(p2, tag('DaneIdentyfikacyjne'))
    if invoice.buyer_nip:
        ET.SubElement(ds2, tag('NIP')).text = invoice.buyer_nip
    ET.SubElement(ds2, tag('PelnaNazwa')).text = invoice.buyer_name or 'Brak danych'
    if invoice.buyer_address:
        adres2 = ET.SubElement(p2, tag('Adres'))
        ET.SubElement(adres2, tag('AdresL1')).text = invoice.buyer_address

    # ── Fa (dane faktury) ─────────────────────────────────────────────────
    fa = ET.SubElement(root, tag('Fa'))
    ET.SubElement(fa, tag('KodWaluty')).text = 'PLN'
    ET.SubElement(fa, tag('P_1')).text = invoice.issue_date.strftime('%Y-%m-%d')
    ET.SubElement(fa, tag('P_2')).text = invoice.invoice_number
    ET.SubElement(fa, tag('P_6')).text = invoice.issue_date.strftime('%Y-%m-%d')

    if is_correction and invoice.corrected_invoice:
        ET.SubElement(fa, tag('RodzajFaktury')).text = 'KOR'
        korFa = ET.SubElement(fa, tag('DaneFaKorygowanej'))
        ET.SubElement(korFa, tag('DataWystFaKorygowanej')).text = (
            invoice.corrected_invoice.issue_date.strftime('%Y-%m-%d')
        )
        ET.SubElement(korFa, tag('NrFaKorygowanej')).text = (
            invoice.corrected_invoice.invoice_number
        )
        if invoice.corrected_invoice.ksef_reference_number:
            ET.SubElement(korFa, tag('NrKSeFFaKorygowanej')).text = (
                invoice.corrected_invoice.ksef_reference_number
            )
        if invoice.correction_reason:
            ET.SubElement(fa, tag('PrzyczynaKorekty')).text = invoice.correction_reason
    else:
        ET.SubElement(fa, tag('RodzajFaktury')).text = 'VAT'

    # Pozycja faktury
    fawiersze = ET.SubElement(fa, tag('FaWiersz'))
    ET.SubElement(fawiersze, tag('NrWierszaFa')).text = '1'
    ET.SubElement(fawiersze, tag('P_7')).text = invoice.service_name
    ET.SubElement(fawiersze, tag('P_8A')).text = 'szt'
    ET.SubElement(fawiersze, tag('P_8B')).text = '1'
    ET.SubElement(fawiersze, tag('P_9A')).text = str(invoice.net_amount)
    ET.SubElement(fawiersze, tag('P_11')).text = str(invoice.net_amount)
    ET.SubElement(fawiersze, tag('P_12')).text = '23'

    # Sumy
    ET.SubElement(fa, tag('P_13_1')).text = str(invoice.net_amount)
    ET.SubElement(fa, tag('P_14_1')).text = str(invoice.vat_amount)
    ET.SubElement(fa, tag('P_15')).text   = str(invoice.gross_amount)

    # Adnotacje
    adnotacje = ET.SubElement(fa, tag('Adnotacje'))
    ET.SubElement(adnotacje, tag('P_16')).text = '2'
    ET.SubElement(adnotacje, tag('P_17')).text = '1'
    ET.SubElement(adnotacje, tag('P_18')).text = '1'

    # Płatność
    if invoice.payment_terms != 'paid':
        platn = ET.SubElement(fa, tag('Platnosc'))
        ET.SubElement(platn, tag('Zaplacono')).text = '0'
        termin = ET.SubElement(platn, tag('TerminPlatnosci'))
        ET.SubElement(termin, tag('Termin')).text = invoice.issue_date.strftime('%Y-%m-%d')
        rach = ET.SubElement(platn, tag('RachunekBankowy'))
        ET.SubElement(rach, tag('NrRB')).text = seller['bank_account'].replace(' ', '')
        ET.SubElement(rach, tag('NazwaBanku')).text = 'PKO BP'

    # ── Stopka ───────────────────────────────────────────────────────────
    stopka = ET.SubElement(root, tag('Stopka'))
    ET.SubElement(stopka, tag('Interoperacyjnosc')).text = '1'

    xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    logger.debug("KSeF: wygenerowano XML FA(3) %d bajtów dla faktury %s",
                 len(xml_bytes), invoice.invoice_number)
    return xml_bytes


# ===========================================================================
# Sesja online + wysyłka faktury
# ===========================================================================

def _open_online_session(access_token: str, aes_key: bytes, aes_iv: bytes) -> str:
    """
    Otwiera sesję interaktywną KSeF API 2.0.
    Zwraca referenceNumber sesji.
    """
    encrypted_key_b64 = _rsa_oaep_encrypt(aes_key)
    iv_b64 = base64.b64encode(aes_iv).decode('ascii')

    resp = requests.post(
        _api_url("/sessions/online"),
        json={
            "formCode": {
                "systemCode":    "FA (3)",
                "schemaVersion": "1-0E",
                "value":         "FA",
            },
            "encryption": {
                "encryptedSymmetricKey": encrypted_key_b64,
                "initializationVector":  iv_b64,
            },
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        },
        timeout=20,
    )
    logger.debug("KSeF /sessions/online status=%d body=%s",
                 resp.status_code, resp.text[:500])
    try:
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.error("KSeF /sessions/online — odpowiedź: %s", resp.text[:500])
        raise

    session_ref = data["referenceNumber"]
    logger.info("KSeF: sesja online otwarta, ref=%s", session_ref)
    return session_ref


def _send_invoice_to_session(
    access_token: str,
    session_ref: str,
    xml_bytes: bytes,
    aes_key: bytes,
    aes_iv: bytes,
) -> str:
    """
    Szyfruje fakturę AES-256-CBC i wysyła do sesji.
    Zwraca referenceNumber faktury.
    """
    encrypted_xml = _aes_encrypt(aes_key, aes_iv, xml_bytes)

    invoice_hash_b64      = base64.b64encode(hashlib.sha256(xml_bytes).digest()).decode('ascii')
    encrypted_hash_b64    = base64.b64encode(hashlib.sha256(encrypted_xml).digest()).decode('ascii')
    encrypted_content_b64 = base64.b64encode(encrypted_xml).decode('ascii')

    resp = requests.post(
        _api_url(f"/sessions/online/{session_ref}/invoices"),
        json={
            "invoiceHash":             invoice_hash_b64,
            "invoiceSize":             len(xml_bytes),
            "encryptedInvoiceHash":    encrypted_hash_b64,
            "encryptedInvoiceSize":    len(encrypted_xml),
            "encryptedInvoiceContent": encrypted_content_b64,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        },
        timeout=30,
    )
    logger.debug("KSeF /sessions/online/{ref}/invoices status=%d body=%s",
                 resp.status_code, resp.text[:500])
    try:
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.error("KSeF /invoices — odpowiedź: %s", resp.text[:500])
        raise

    ref = data["referenceNumber"]
    logger.info("KSeF: faktura wysłana do sesji, invoice_ref=%s", ref)
    return ref


def _close_online_session(access_token: str, session_ref: str) -> None:
    """Zamknij sesję interaktywną (uruchamia generowanie zbiorczego UPO)."""
    try:
        resp = requests.post(
            _api_url(f"/sessions/online/{session_ref}/close"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept":        "application/json",
            },
            timeout=15,
        )
        logger.debug("KSeF close session status=%d body=%s",
                     resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("KSeF: nie udało się zamknąć sesji online %s: %s", session_ref, e)


def _poll_invoice_status(access_token: str, invoice_ref: str) -> dict:
    """
    Polluje status faktury aż do akceptacji lub odrzucenia.
    Zwraca dict: {'status': 'accepted'|'rejected', 'ksef_ref': '...'}
    """
    for attempt in range(UPO_MAX_RETRIES):
        resp = requests.get(
            _api_url(f"/invoices/{invoice_ref}/status"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept":        "application/json",
            },
            timeout=15,
        )
        if not resp.ok:
            logger.warning("KSeF invoice/status błąd %d (próba %d): %s",
                           resp.status_code, attempt + 1, resp.text[:300])
            time.sleep(UPO_RETRY_DELAY)
            continue

        data = resp.json()
        logger.debug("KSeF invoice/status (próba %d): %s", attempt + 1, data)

        # Obsługa różnych formatów odpowiedzi
        code = (
            data.get("processingCode")
            or data.get("status", {}).get("code")
        )
        ksef_ref = (
            data.get("ksefReferenceNumber")
            or data.get("elementReferenceNumber")
            or invoice_ref
        )

        if code == 200:
            return {'status': 'accepted', 'ksef_ref': ksef_ref}
        if code and int(code) >= 400:
            reason = (
                data.get("processingDescription")
                or data.get("status", {}).get("description", "")
            )
            logger.error("KSeF: faktura odrzucona: %s", reason)
            return {'status': 'rejected', 'ksef_ref': ksef_ref, 'reason': reason}

        time.sleep(UPO_RETRY_DELAY)

    raise TimeoutError(
        f"KSeF: timeout oczekiwania na akceptację faktury ({UPO_MAX_RETRIES * UPO_RETRY_DELAY}s)"
    )


# ===========================================================================
# Publiczny interfejs
# ===========================================================================

def _do_submit(invoice, is_correction: bool) -> None:
    """Wspólna logika wysyłki faktury/korekty."""
    access_token = None
    session_ref  = None

    try:
        access_token = _get_access_token()

        # Każda sesja dostaje swój unikatowy klucz AES i IV
        aes_key = os.urandom(32)   # AES-256
        aes_iv  = os.urandom(16)   # CBC IV

        session_ref  = _open_online_session(access_token, aes_key, aes_iv)
        
        # Krótka pauza, aby upewnić się, że sesja jest aktywna w systemie KSeF
        time.sleep(2)

        xml_bytes    = _build_fa3_xml(invoice, is_correction=is_correction)
        invoice_ref  = _send_invoice_to_session(access_token, session_ref, xml_bytes, aes_key, aes_iv)

        _close_online_session(access_token, session_ref)
        session_ref = None  # zamknięta — nie zamykaj ponownie w finally

        result = _poll_invoice_status(access_token, invoice_ref)

        if result['status'] == 'accepted':
            invoice.ksef_status           = "accepted"
            invoice.ksef_reference_number = result['ksef_ref']
            invoice.save(update_fields=["ksef_status", "ksef_reference_number"])
            logger.info("KSeF: faktura %s zaakceptowana, ref=%s",
                        invoice.invoice_number, result['ksef_ref'])
        else:
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
            raise RuntimeError(
                f"Faktura odrzucona przez KSeF: {result.get('reason', 'nieznany powód')}"
            )

    except Exception:
        if invoice.ksef_status == "sent":
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
        raise
    finally:
        if session_ref and access_token:
            _close_online_session(access_token, session_ref)
        if access_token:
            _close_auth_session(access_token)


def submit(invoice) -> None:
    """Wysyła fakturę do KSeF API 2.0 i oczekuje na akceptację."""
    logger.info("KSeF: wysyłam fakturę %s (brutto=%.2f PLN)",
                invoice.invoice_number, float(invoice.gross_amount))
    invoice.ksef_status = "sent"
    invoice.save(update_fields=["ksef_status"])
    try:
        _do_submit(invoice, is_correction=False)
        invoice.user.premium += invoice.points_added
        invoice.user.save(update_fields=["premium"])
        logger.info("KSeF: użytkownik %s +%d pkt (saldo=%d)",
                    invoice.user.email, invoice.points_added, invoice.user.premium)
    except Exception as exc:
        logger.error("KSeF submit błąd dla %s: %s", invoice.invoice_number, exc)
        raise


def submit_correction(correction_invoice) -> None:
    """Wysyła fakturę korygującą FA(3) do KSeF API 2.0."""
    logger.info("KSeF: wysyłam korektę %s do faktury %s",
                correction_invoice.invoice_number,
                correction_invoice.corrected_invoice.invoice_number
                if correction_invoice.corrected_invoice else '?')
    correction_invoice.ksef_status = "sent"
    correction_invoice.save(update_fields=["ksef_status"])
    try:
        _do_submit(correction_invoice, is_correction=True)
    except Exception as exc:
        logger.error("KSeF submit_correction błąd: %s", exc)
        raise
