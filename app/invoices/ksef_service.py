"""
Serwis KSeF (Krajowy System e-Faktur) — integracja z API 2.0.

Implementacja oparta na stanach KSeF:
1. Autoryzacja (challenge -> token -> polling statusu 200 -> redeem).
2. Sesja interaktywna (online):
   - Otwarcie sesji.
   - Polling statusu sesji do kodu 200 (Gotowość).
   - Wysyłka zaszyfrowanej faktury XML FA(3).
   - Zamknięcie sesji.
   - Polling statusu sesji do kodu 700 (Zakończenie przetwarzania).
3. Pobranie statusu faktury (polling do kodu 200/4xx, obsługa 404).

Wymagania:
    pip install cryptography requests

Konfiguracja (.env):
  KSEF_SANDBOX = True/False
  KSEF_NIP     = NIP firmy
  KSEF_TOKEN   = token serwisowy
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

# Ustawienia pollingu
UPO_MAX_RETRIES = 60  # max 3 minuty dla każdego etapu
UPO_RETRY_DELAY = 3   # sekundy

# Namespace FA(3)
FA3_NS = 'http://crd.gov.pl/wzor/2025/06/25/13775/'


def _api_url(path: str) -> str:
    return f"{settings.KSEF_API_URL}{path}"


# ===========================================================================
# Helper: Zapytania z Retry (Exponential Backoff)
# ===========================================================================

def _ksef_request(method: str, path: str, **kwargs) -> requests.Response:
    """
    Wykonuje zapytanie do KSeF z retry dla błędów sieciowych i 5xx.
    Nie ponawia dla 4xx (błędy logiki/danych).
    """
    max_attempts = 5
    base_delay = 1.0

    for attempt in range(max_attempts):
        try:
            resp = requests.request(method, _api_url(path), timeout=25, **kwargs)
            
            # Jeśli 5xx (serwer KSeF przeciążony), ponawiamy
            if 500 <= resp.status_code < 600:
                logger.warning("KSeF %d na %s (próba %d/%d): %s",
                               resp.status_code, path, attempt + 1, max_attempts, resp.text[:200])
            else:
                return resp
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            logger.warning("KSeF błąd połączenia %s (próba %d/%d): %s",
                           path, attempt + 1, max_attempts, e)
        
        if attempt < max_attempts - 1:
            time.sleep(base_delay * (2 ** attempt))
    
    # Ostatnia próba — rzuci wyjątek lub zwróci błąd
    return requests.request(method, _api_url(path), timeout=25, **kwargs)


# ===========================================================================
# Bezpieczeństwo (RSA, AES)
# ===========================================================================

_cached_public_key = None

def _get_mf_public_key():
    global _cached_public_key
    if _cached_public_key: return _cached_public_key

    resp = _ksef_request("GET", "/security/public-key-certificates", headers={"Accept": "application/json"})
    resp.raise_for_status()
    certs = resp.json()
    cert_data = next((c.get('certificate') for c in certs if 'Symmetric' in str(c.get('usage', ''))), certs[0].get('certificate'))

    try:
        cert = load_der_x509_certificate(base64.b64decode(cert_data))
    except Exception:
        cert = load_pem_x509_certificate(cert_data.encode())

    _cached_public_key = cert.public_key()
    return _cached_public_key


def _rsa_oaep_encrypt(data: bytes) -> str:
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


def _aes_encrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()


# ===========================================================================
# Autoryzacja
# ===========================================================================

def _get_access_token() -> str:
    nip = settings.KSEF_NIP
    token = settings.KSEF_TOKEN
    if not nip or not token: raise ValueError("Brak KSEF_NIP/KSEF_TOKEN")

    logger.info("KSeF: Autoryzacja NIP=%s", nip)

    # 1. Challenge
    resp = _ksef_request("POST", "/auth/challenge")
    resp.raise_for_status()
    cd = resp.json()
    challenge, ts = cd["challenge"], cd["timestampMs"]

    # 2. Encrypt
    enc_token = _rsa_oaep_encrypt(f"{token}|{ts}".encode('utf-8'))

    # 3. Ksef-token
    resp = _ksef_request("POST", "/auth/ksef-token", json={
        "challenge": challenge,
        "contextIdentifier": {"type": "Nip", "value": nip},
        "encryptedToken": enc_token,
    })
    resp.raise_for_status()
    ad = resp.json()
    auth_token = ad["authenticationToken"]["token"]
    ref_no = ad["referenceNumber"]

    # 4. Polling statusu autoryzacji (200)
    for _ in range(UPO_MAX_RETRIES):
        resp = _ksef_request("GET", f"/auth/{ref_no}", headers={"Authorization": f"Bearer {auth_token}"})
        resp.raise_for_status()
        code = resp.json().get("status", {}).get("code")
        if code == 200: break
        if code and code >= 400: raise RuntimeError(f"KSeF Auth Error: {code}")
        time.sleep(UPO_RETRY_DELAY)
    else: raise TimeoutError("KSeF Auth Timeout")

    # 5. Redeem
    resp = _ksef_request("POST", "/auth/token/redeem", headers={"Authorization": f"Bearer {auth_token}"})
    resp.raise_for_status()
    at = resp.json()["accessToken"]["token"]
    logger.info("KSeF: Uzyskano accessToken")
    return at


def _close_auth_session(at: str):
    try: _ksef_request("DELETE", "/auth/sessions/current", headers={"Authorization": f"Bearer {at}"})
    except Exception: pass


# ===========================================================================
# Obsługa sesji i faktur
# ===========================================================================

def _wait_for_session_status(at: str, session_ref: str, target: int):
    """Czeka na konkretny stan sesji (np. 200-Gotowa, 700-Zakończona)."""
    for _ in range(UPO_MAX_RETRIES):
        resp = _ksef_request("GET", f"/sessions/online/{session_ref}", headers={"Authorization": f"Bearer {at}"})
        resp.raise_for_status()
        code = resp.json().get("status", {}).get("code")
        if code == target: return
        if code and code >= 400 and code != 415:
            raise RuntimeError(f"KSeF Session {session_ref} Error: {code}")
        time.sleep(UPO_RETRY_DELAY)
    raise TimeoutError(f"KSeF Session {session_ref} Timeout (target {target})")


def _open_session(at: str, key: bytes, iv: bytes) -> str:
    resp = _ksef_request("POST", "/sessions/online", json={
        "formCode": {"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"},
        "encryption": {"encryptedSymmetricKey": _rsa_oaep_encrypt(key), "initializationVector": base64.b64encode(iv).decode('ascii')},
    }, headers={"Authorization": f"Bearer {at}"})
    resp.raise_for_status()
    s_ref = resp.json()["referenceNumber"]
    logger.info("KSeF: Sesja %s otwarta, czekam na 200...", s_ref)
    _wait_for_session_status(at, s_ref, 200)
    return s_ref


def _send_invoice(at: str, s_ref: str, xml: bytes, key: bytes, iv: bytes) -> str:
    enc_xml = _aes_encrypt(key, iv, xml)
    resp = _ksef_request("POST", f"/sessions/online/{s_ref}/invoices", json={
        "invoiceHash": base64.b64encode(hashlib.sha256(xml).digest()).decode('ascii'),
        "invoiceSize": len(xml),
        "encryptedInvoiceHash": base64.b64encode(hashlib.sha256(enc_xml).digest()).decode('ascii'),
        "encryptedInvoiceSize": len(enc_xml),
        "encryptedInvoiceContent": base64.b64encode(enc_xml).decode('ascii'),
    }, headers={"Authorization": f"Bearer {at}"})
    resp.raise_for_status()
    i_ref = resp.json()["referenceNumber"]
    logger.info("KSeF: Faktura wysłana, ref=%s", i_ref)
    return i_ref


def _close_session(at: str, s_ref: str):
    _ksef_request("POST", f"/sessions/online/{s_ref}/close", headers={"Authorization": f"Bearer {at}"})
    logger.info("KSeF: Sesja %s zamknięta, czekam na 700...", s_ref)
    _wait_for_session_status(at, s_ref, 700)


def _poll_invoice_status(at: str, i_ref: str) -> dict:
    """Pobiera status faktury. Obsługuje 404 (polling)."""
    for _ in range(UPO_MAX_RETRIES):
        resp = _ksef_request("GET", f"/invoices/{i_ref}/status", headers={"Authorization": f"Bearer {at}"})
        if resp.status_code == 404:
            time.sleep(UPO_RETRY_DELAY)
            continue
        
        resp.raise_for_status()
        data = resp.json()
        code = data.get("processingCode") or data.get("status", {}).get("code")
        k_ref = data.get("ksefReferenceNumber") or i_ref

        if code == 200: return {"status": "accepted", "ksef_ref": k_ref}
        if code and int(code) >= 400:
            return {"status": "rejected", "reason": data.get("processingDescription", "Błąd")}
        
        time.sleep(UPO_RETRY_DELAY)
    raise TimeoutError("KSeF Invoice Polling Timeout")


# ===========================================================================
# XML FA(3)
# ===========================================================================

def _build_fa3_xml(invoice, is_correction: bool = False) -> bytes:
    seller = settings.INVOICE_SELLER_DATA
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    ET.register_namespace('', FA3_NS)
    tag = lambda n: f'{{{FA3_NS}}}{n}'

    root = ET.Element(tag('Faktura'), xmlns=FA3_NS)
    
    nagl = ET.SubElement(root, tag('Naglowek'))
    ET.SubElement(nagl, tag('KodFormularza'), kodSystemowy="FA (3)", wersjaSchemy="1-0E").text = "FA"
    ET.SubElement(nagl, tag('WariantFormularza')).text = "3"
    ET.SubElement(nagl, tag('DataWytworzeniaFa')).text = now_str
    ET.SubElement(nagl, tag('SystemInfo')).text = "wyznaczresurs.pl v2.0"

    p1 = ET.SubElement(root, tag('Podmiot1'))
    ds1 = ET.SubElement(p1, tag('DaneIdentyfikacyjne'))
    ET.SubElement(ds1, tag('NIP')).text = seller['nip']
    ET.SubElement(ds1, tag('PelnaNazwa')).text = seller['name']
    adres1 = ET.SubElement(p1, tag('Adres'))
    ET.SubElement(adres1, tag('AdresL1')).text = seller['address']

    p2 = ET.SubElement(root, tag('Podmiot2'))
    ds2 = ET.SubElement(p2, tag('DaneIdentyfikacyjne'))
    if invoice.buyer_nip: ET.SubElement(ds2, tag('NIP')).text = invoice.buyer_nip
    ET.SubElement(ds2, tag('PelnaNazwa')).text = invoice.buyer_name or 'Brak danych'
    if invoice.buyer_address:
        adres2 = ET.SubElement(p2, tag('Adres'))
        ET.SubElement(adres2, tag('AdresL1')).text = invoice.buyer_address

    fa = ET.SubElement(root, tag('Fa'))
    ET.SubElement(fa, tag('KodWaluty')).text = 'PLN'
    ET.SubElement(fa, tag('P_1')).text = invoice.issue_date.strftime('%Y-%m-%d')
    ET.SubElement(fa, tag('P_2')).text = invoice.invoice_number
    ET.SubElement(fa, tag('P_6')).text = invoice.issue_date.strftime('%Y-%m-%d')
    ET.SubElement(fa, tag('RodzajFaktury')).text = 'KOR' if is_correction else 'VAT'

    if is_correction and invoice.corrected_invoice:
        k_fa = ET.SubElement(fa, tag('DaneFaKorygowanej'))
        ET.SubElement(k_fa, tag('DataWystFaKorygowanej')).text = invoice.corrected_invoice.issue_date.strftime('%Y-%m-%d')
        ET.SubElement(k_fa, tag('NrFaKorygowanej')).text = invoice.corrected_invoice.invoice_number
        if invoice.corrected_invoice.ksef_reference_number:
            ET.SubElement(k_fa, tag('NrKSeFFaKorygowanej')).text = invoice.corrected_invoice.ksef_reference_number
        if invoice.correction_reason: ET.SubElement(fa, tag('PrzyczynaKorekty')).text = invoice.correction_reason

    w = ET.SubElement(fa, tag('FaWiersz'))
    ET.SubElement(w, tag('NrWierszaFa')).text = '1'
    ET.SubElement(w, tag('P_7')).text = invoice.service_name
    ET.SubElement(w, tag('P_8A')).text = 'szt'
    ET.SubElement(w, tag('P_8B')).text = '1'
    ET.SubElement(w, tag('P_9A')).text = str(invoice.net_amount)
    ET.SubElement(w, tag('P_11')).text = str(invoice.net_amount)
    ET.SubElement(w, tag('P_12')).text = '23'

    ET.SubElement(fa, tag('P_13_1')).text = str(invoice.net_amount)
    ET.SubElement(fa, tag('P_14_1')).text = str(invoice.vat_amount)
    ET.SubElement(fa, tag('P_15')).text   = str(invoice.gross_amount)

    adn = ET.SubElement(fa, tag('Adnotacje'))
    for p in ['P_16', 'P_17', 'P_18']: ET.SubElement(adn, tag(p)).text = '2' if p == 'P_16' else '1'

    if invoice.payment_terms != 'paid':
        platn = ET.SubElement(fa, tag('Platnosc'))
        ET.SubElement(platn, tag('Zaplacono')).text = '0'
        ET.SubElement(ET.SubElement(platn, tag('TerminPlatnosci')), tag('Termin')).text = invoice.issue_date.strftime('%Y-%m-%d')
        rach = ET.SubElement(platn, tag('RachunekBankowy'))
        ET.SubElement(rach, tag('NrRB')).text = seller['bank_account'].replace(' ', '')
        ET.SubElement(rach, tag('NazwaBanku')).text = 'PKO BP'

    stopka = ET.SubElement(root, tag('Stopka'))
    ET.SubElement(stopka, tag('Interoperacyjnosc')).text = '1'

    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


# ===========================================================================
# Public API
# ===========================================================================

def _do_submit(invoice, is_correction: bool):
    at, s_ref = None, None
    try:
        at = _get_access_token()
        key, iv = os.urandom(32), os.urandom(16)
        
        s_ref = _open_session(at, key, iv)
        xml = _build_fa3_xml(invoice, is_correction)
        i_ref = _send_invoice(at, s_ref, xml, key, iv)
        
        _close_session(at, s_ref)
        s_ref = None
        
        res = _poll_invoice_status(at, i_ref)
        if res['status'] == 'accepted':
            invoice.ksef_status = "accepted"
            invoice.ksef_reference_number = res['ksef_ref']
            invoice.save(update_fields=["ksef_status", "ksef_reference_number"])
        else:
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
            raise RuntimeError(f"Odrzucona: {res.get('reason')}")

    except Exception:
        if invoice.ksef_status == "sent":
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
        raise
    finally:
        if at:
            if s_ref: 
                try: _ksef_request("POST", f"/sessions/online/{s_ref}/close", headers={"Authorization": f"Bearer {at}"})
                except Exception: pass
            _close_auth_session(at)


def submit(invoice):
    logger.info("KSeF: Wysyłka %s", invoice.invoice_number)
    invoice.ksef_status = "sent"
    invoice.save(update_fields=["ksef_status"])
    try:
        _do_submit(invoice, False)
        invoice.user.premium += invoice.points_added
        invoice.user.save(update_fields=["premium"])
    except Exception as e:
        logger.error("KSeF Submit Error %s: %s", invoice.invoice_number, e)
        raise


def submit_correction(invoice):
    logger.info("KSeF: Wysyłka korekty %s", invoice.invoice_number)
    invoice.ksef_status = "sent"
    invoice.save(update_fields=["ksef_status"])
    try:
        _do_submit(invoice, True)
    except Exception as e:
        logger.error("KSeF Correction Error: %s", e)
        raise
