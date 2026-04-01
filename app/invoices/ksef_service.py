"""
Serwis KSeF (Krajowy System e-Faktur) — prawdziwa integracja z API Ministerstwa Finansów.

Obsługuje:
  - Autoryzację tokenem serwisowym (bez podpisu XAdES)
  - Generowanie XML faktury w formacie FA(2)
  - Wysyłkę do KSeF i polling UPO (UrzędowePotwierdzenie Odbioru)
  - Faktury korygujące FA(2)

Konfiguracja (.env):
  KSEF_SANDBOX = True/False
  KSEF_NIP     = NIP firmy (10 cyfr)
  KSEF_TOKEN   = token serwisowy z panelu KSeF
  KSEF_API_URL = ustawiany automatycznie na podstawie KSEF_SANDBOX
"""
import hashlib
import base64
import logging
import time
import uuid
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import requests
from django.conf import settings
from django.utils import timezone as django_tz

logger = logging.getLogger('invoices.ksef')

# Maksymalna liczba prób pollingu UPO (co 3 sekundy)
UPO_MAX_RETRIES = 20
UPO_RETRY_DELAY = 3  # sekundy

# Namespace FA(2)
FA2_NS = 'http://crd.gov.pl/wzor/2023/06/29/9781/'


# ===========================================================================
# Sesja KSeF (token serwisowy)
# ===========================================================================

def _api_url(path: str) -> str:
    return f"{settings.KSEF_API_URL}{path}"


def _get_session_token() -> str:
    """
    Autoryzuje się w KSeF tokenem serwisowym i zwraca token sesyjny.

    Przepływ (token serwisowy, bez XAdES):
    1. POST /api/online/Session/AuthorisationChallenge → challenge
    2. Oblicz: SHA-256(hex_decode(challenge) || token_bytes)
    3. POST /api/online/Session/InitialisationToken → session_token
    """
    nip   = settings.KSEF_NIP
    token = settings.KSEF_TOKEN

    if not nip or not token:
        raise ValueError("KSEF_NIP lub KSEF_TOKEN nie są skonfigurowane w .env")

    logger.info("KSeF: rozpoczynam autoryzację (sandbox=%s, NIP=%s)", settings.KSEF_SANDBOX, nip)

    # Krok 1: AuthorisationChallenge
    challenge_resp = requests.post(
        _api_url("/api/online/Session/AuthorisationChallenge"),
        json={"contextIdentifier": {"type": "onip", "identifier": nip}},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=15,
    )
    if not challenge_resp.ok:
        logger.error("KSeF AuthorisationChallenge błąd %d: %s",
                     challenge_resp.status_code, challenge_resp.text[:300])
        challenge_resp.raise_for_status()

    challenge_data = challenge_resp.json()
    challenge_hex  = challenge_data["challenge"]     # np. "0000000012345678901234567890"
    timestamp      = challenge_data["timestamp"]     # ISO datetime
    logger.debug("KSeF: challenge=%s timestamp=%s", challenge_hex[:16], timestamp)

    # Krok 2: Oblicz skrót tokenu
    # Format: SHA-256(bytes_from_hex(challenge) || token_bytes_utf8)
    try:
        challenge_bytes = bytes.fromhex(challenge_hex)
    except ValueError:
        # Jeśli challenge nie jest hex — traktuj jako UTF-8
        challenge_bytes = challenge_hex.encode('utf-8')

    token_bytes    = token.encode('utf-8')
    token_hash     = hashlib.sha256(challenge_bytes + token_bytes).digest()
    token_b64      = base64.b64encode(token_hash).decode('ascii')

    # Krok 3: InitialisationToken
    init_resp = requests.post(
        _api_url("/api/online/Session/InitialisationToken"),
        json={
            "contextIdentifier": {"type": "onip", "identifier": nip},
            "credentialIdentifier": None,
            "token": token_b64,
        },
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=15,
    )
    if not init_resp.ok:
        logger.error("KSeF InitialisationToken błąd %d: %s",
                     init_resp.status_code, init_resp.text[:300])
        init_resp.raise_for_status()

    session_token = init_resp.json().get("sessionToken", {}).get("token")
    if not session_token:
        raise ValueError(f"KSeF nie zwrócił sessionToken: {init_resp.text[:200]}")

    logger.info("KSeF: sesja zainicjowana, token=%s...", session_token[:12])
    return session_token


def _close_session(session_token: str) -> None:
    """Zamknij sesję KSeF po zakończeniu pracy."""
    try:
        requests.get(
            _api_url("/api/online/Session/Terminate"),
            headers={"X-Session-Token": session_token, "Accept": "application/json"},
            timeout=10,
        )
        logger.debug("KSeF: sesja zamknięta")
    except Exception as e:
        logger.warning("KSeF: nie udało się zamknąć sesji: %s", e)


# ===========================================================================
# Generowanie XML FA(2)
# ===========================================================================

def _seller_data() -> dict:
    return settings.INVOICE_SELLER_DATA


def _build_fa2_xml(invoice, is_correction: bool = False) -> bytes:
    """
    Buduje minimalny poprawny XML FA(2) dla danej faktury.
    Zwraca zakodowany XML jako bytes (UTF-8).

    Dokumentacja FA(2): https://www.gov.pl/web/kas/struktury-dokumentow-xml
    """
    seller = _seller_data()
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Rejestracja namespace bez prefiksu
    ET.register_namespace('', FA2_NS)
    ns = FA2_NS

    def tag(name):
        return f'{{{ns}}}{name}'

    root = ET.Element(tag('Faktura'))
    root.set('xmlns', ns)

    # ── Nagłówek ─────────────────────────────────────────────────────────
    nagl = ET.SubElement(root, tag('Naglowek'))
    ET.SubElement(nagl, tag('KodFormularza'),
                  kodSystemowy="FA (2)", wersjaSchemy="1-0E").text = "FA"
    ET.SubElement(nagl, tag('WariantFormularza')).text = "2"
    ET.SubElement(nagl, tag('DataWytworzeniaFa')).text = now_str
    ET.SubElement(nagl, tag('SystemInfo')).text = "wyznaczresurs.pl v1.0"

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
    ET.SubElement(fa, tag('P_6')).text = invoice.issue_date.strftime('%Y-%m-%d')  # data dostawy

    if is_correction and invoice.corrected_invoice:
        ET.SubElement(fa, tag('RodzajFaktury')).text = 'KOR'
        korFa = ET.SubElement(fa, tag('DaneFaKorygowanej'))
        ET.SubElement(korFa, tag('DataWystFaKorygowanej')).text = (
            invoice.corrected_invoice.issue_date.strftime('%Y-%m-%d')
        )
        ET.SubElement(korFa, tag('NrFaKorygowanej')).text = invoice.corrected_invoice.invoice_number
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
    ET.SubElement(fawiersze, tag('P_8A')).text = 'szt'   # jednostka miary
    ET.SubElement(fawiersze, tag('P_8B')).text = '1'     # ilość
    ET.SubElement(fawiersze, tag('P_9A')).text = str(invoice.net_amount)  # cena netto
    ET.SubElement(fawiersze, tag('P_11')).text = str(invoice.net_amount)  # wartość netto
    ET.SubElement(fawiersze, tag('P_12')).text = '23'    # stawka VAT %
    ET.SubElement(fawiersze, tag('GTU')).text = 'GTU_12' # Usługi niematerialne

    # Sumy
    ET.SubElement(fa, tag('P_13_1')).text = str(invoice.net_amount)   # netto 23%
    ET.SubElement(fa, tag('P_14_1')).text = str(invoice.vat_amount)   # VAT 23%
    ET.SubElement(fa, tag('P_15')).text   = str(invoice.gross_amount)  # razem brutto

    # Warunki płatności
    zaplata = ET.SubElement(fa, tag('Adnotacje'))
    ET.SubElement(zaplata, tag('P_16')).text = '2'  # 2 = zapłacono przelewem
    ET.SubElement(zaplata, tag('P_17')).text = '1'  # 1 = metoda kasowa nie obowiązuje
    ET.SubElement(zaplata, tag('P_18')).text = '1'  # 1 = samofakturowanie — NIE

    # Rachunek bankowy (dla faktur do zapłaty)
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
    logger.debug("KSeF: wygenerowano XML %d bajtów dla faktury %s",
                 len(xml_bytes), invoice.invoice_number)
    return xml_bytes


# ===========================================================================
# Wysyłka faktury i polling UPO
# ===========================================================================

def _send_invoice(session_token: str, xml_bytes: bytes) -> str:
    """
    Wysyła fakturę XML do KSeF.
    Zwraca referenceNumber (do pollingu UPO).
    """
    xml_b64 = base64.b64encode(xml_bytes).decode('ascii')

    resp = requests.post(
        _api_url("/api/online/Invoice/Send"),
        json={
            "invoiceHash": {
                "fileSize": len(xml_bytes),
                "hashSHA": {
                    "algorithm": "SHA-256",
                    "encoding":  "Base64",
                    "value": base64.b64encode(
                        hashlib.sha256(xml_bytes).digest()
                    ).decode('ascii'),
                },
            },
            "invoicePayload": {
                "type":            "plain",
                "invoiceBody":     xml_b64,
                "invoiceBodySize": len(xml_bytes),
            },
        },
        headers={
            "X-Session-Token": session_token,
            "Content-Type":    "application/json",
            "Accept":          "application/json",
        },
        timeout=30,
    )
    if not resp.ok:
        logger.error("KSeF Send błąd %d: %s", resp.status_code, resp.text[:300])
        resp.raise_for_status()

    ref = resp.json().get("referenceNumber")
    logger.info("KSeF: faktura wysłana, referenceNumber=%s", ref)
    return ref


def _poll_upo(session_token: str, reference_number: str) -> dict:
    """
    Polluje status faktury do uzyskania UPO (accepted/rejected).
    Zwraca dict: {'status': 'accepted'|'rejected', 'ksef_ref': '...'}
    """
    for attempt in range(UPO_MAX_RETRIES):
        resp = requests.get(
            _api_url(f"/api/online/Invoice/Status/{reference_number}"),
            headers={
                "X-Session-Token": session_token,
                "Accept":          "application/json",
            },
            timeout=15,
        )
        if not resp.ok:
            logger.warning("KSeF Status błąd %d (próba %d): %s",
                           resp.status_code, attempt + 1, resp.text[:200])
            time.sleep(UPO_RETRY_DELAY)
            continue

        data = resp.json()
        processing_code = data.get("processingCode")
        ksef_ref        = data.get("elementReferenceNumber", reference_number)

        logger.debug("KSeF Status (próba %d): processingCode=%s", attempt + 1, processing_code)

        # processingCode: 200 = accepted, 400 = rejected, inne = w toku
        if processing_code == 200:
            return {'status': 'accepted', 'ksef_ref': ksef_ref}
        if processing_code == 400:
            reason = data.get("processingDescription", "")
            logger.error("KSeF: faktura odrzucona: %s", reason)
            return {'status': 'rejected', 'ksef_ref': ksef_ref, 'reason': reason}

        time.sleep(UPO_RETRY_DELAY)

    raise TimeoutError(
        f"KSeF: przekroczono limit oczekiwania na UPO ({UPO_MAX_RETRIES * UPO_RETRY_DELAY}s)"
    )


# ===========================================================================
# Publiczny interfejs
# ===========================================================================

def submit(invoice) -> None:
    """
    Wysyła fakturę do KSeF i oczekuje na akceptację (UPO).
    Po akceptacji doładowuje punkty użytkownika.
    Modyfikuje invoice in-place i zapisuje zmiany do bazy.
    """
    logger.info("KSeF: wysyłam fakturę %s (brutto=%.2f PLN)",
                invoice.invoice_number, float(invoice.gross_amount))

    invoice.ksef_status = "sent"
    invoice.save(update_fields=["ksef_status"])

    session_token = None
    try:
        session_token  = _get_session_token()
        xml_bytes      = _build_fa2_xml(invoice, is_correction=False)
        reference_num  = _send_invoice(session_token, xml_bytes)
        result         = _poll_upo(session_token, reference_num)

        if result['status'] == 'accepted':
            invoice.ksef_status           = "accepted"
            invoice.ksef_reference_number = result['ksef_ref']
            invoice.save(update_fields=["ksef_status", "ksef_reference_number"])
            logger.info("KSeF: faktura %s zaakceptowana, ref=%s",
                        invoice.invoice_number, result['ksef_ref'])

            invoice.user.premium += invoice.points_added
            invoice.user.save(update_fields=["premium"])
            logger.info("KSeF: użytkownik %s +%d pkt (saldo=%d)",
                        invoice.user.email, invoice.points_added, invoice.user.premium)
        else:
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
            logger.error("KSeF: faktura %s odrzucona: %s",
                         invoice.invoice_number, result.get('reason', ''))
            raise RuntimeError(
                f"Faktura odrzucona przez KSeF: {result.get('reason', 'nieznany powód')}"
            )

    except Exception as exc:
        if invoice.ksef_status == "sent":
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
        logger.error("KSeF submit błąd dla %s: %s", invoice.invoice_number, exc)
        raise
    finally:
        if session_token:
            _close_session(session_token)


def submit_correction(correction_invoice) -> None:
    """
    Wysyła fakturę korygującą FA(2) do KSeF.
    Korekta nie zmienia salda punktów.
    """
    logger.info("KSeF: wysyłam korektę %s do faktury %s",
                correction_invoice.invoice_number,
                correction_invoice.corrected_invoice.invoice_number
                if correction_invoice.corrected_invoice else '?')

    correction_invoice.ksef_status = "sent"
    correction_invoice.save(update_fields=["ksef_status"])

    session_token = None
    try:
        session_token = _get_session_token()
        xml_bytes     = _build_fa2_xml(correction_invoice, is_correction=True)
        reference_num = _send_invoice(session_token, xml_bytes)
        result        = _poll_upo(session_token, reference_num)

        if result['status'] == 'accepted':
            correction_invoice.ksef_status           = "accepted"
            correction_invoice.ksef_reference_number = result['ksef_ref']
            correction_invoice.save(update_fields=["ksef_status", "ksef_reference_number"])
            logger.info("KSeF: korekta %s zaakceptowana, ref=%s",
                        correction_invoice.invoice_number, result['ksef_ref'])
        else:
            correction_invoice.ksef_status = "rejected"
            correction_invoice.save(update_fields=["ksef_status"])
            raise RuntimeError(
                f"Korekta odrzucona przez KSeF: {result.get('reason', 'nieznany powód')}"
            )

    except Exception as exc:
        if correction_invoice.ksef_status == "sent":
            correction_invoice.ksef_status = "rejected"
            correction_invoice.save(update_fields=["ksef_status"])
        logger.error("KSeF submit_correction błąd: %s", exc)
        raise
    finally:
        if session_token:
            _close_session(session_token)
