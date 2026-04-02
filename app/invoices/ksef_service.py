"""
Serwis KSeF (Krajowy System e-Faktur) — Integracja z API 2.0 (FA(3)).
Zgodny z wymogami obowiązującymi od 2026 r.
Refaktoryzacja na podejście obiektowe dla lepszego zarządzania stanem sesji.
"""
import base64
import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from typing import Optional, Dict, Any, Tuple

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import load_der_x509_certificate, load_pem_x509_certificate
from django.conf import settings

logger = logging.getLogger('invoices.ksef')

# Konfiguracja pollingu i limitów czasowych
POLLING_MAX_RETRIES = 60
POLLING_RETRY_DELAY = 3  # sekundy
REQUEST_TIMEOUT = 30     # sekundy

# Namespace dla FA(3) - obowiązujący od 1 lutego 2026 r.
FA3_NS = 'http://crd.gov.pl/wzor/2025/06/25/13775/'


class KSeFError(Exception):
    """Bazowy wyjątek dla błędów integracji z KSeF."""
    def __init__(self, message, status_code=None, response_text=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class KSeFClient:
    """
    Klient API KSeF 2.0 obsługujący sesję interaktywną.
    Zapewnia autentykację JWT, szyfrowanie symetryczne i asymetryczne.
    """

    def __init__(self):
        self.base_url = settings.KSEF_API_URL.rstrip('/')
        self.nip = settings.KSEF_NIP.replace('-', '').strip()
        self.token = settings.KSEF_TOKEN.strip()
        self.session = requests.Session()
        self.access_token = None
        self.session_ref = None
        self.enc_key = None
        self.enc_iv = None
        self._public_key = None

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Wykonywanie zapytań HTTP do API KSeF."""
        url = f"{self.base_url}{path}"
        headers = kwargs.get('headers', {}).copy()
        headers.setdefault('Accept', 'application/json')
        
        if method in ['POST', 'PUT']:
            headers.setdefault('Content-Type', 'application/json')
        
        if self.access_token:
            headers.setdefault('Authorization', f"Bearer {self.access_token}")
        
        kwargs['headers'] = headers
        
        try:
            resp = self.session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
            if not resp.ok:
                logger.warning("KSeF API Response Error %d: %s", resp.status_code, resp.text[:500])
            return resp
        except requests.RequestException as e:
            logger.error("KSeF Request Failed: %s", e)
            raise KSeFError(f"Błąd połączenia z API KSeF: {e}")

    # --- Szyfrowanie (RSA i AES) ---

    def _get_public_key(self):
        """Pobiera i cache'uje klucz publiczny MF do szyfrowania."""
        if self._public_key:
            return self._public_key

        resp = self._request("GET", "/security/public-key-certificates")
        if not resp.ok:
            raise KSeFError("Błąd pobierania certyfikatów MF", resp.status_code, resp.text)
        
        certs = resp.json()
        cert_data = next((c.get('certificate') for c in certs if 'encryption' in str(c.get('usage', '')).lower()), certs[0].get('certificate'))

        try:
            cert_bytes = base64.b64decode(cert_data)
            cert = load_der_x509_certificate(cert_bytes)
        except Exception:
            cert = load_pem_x509_certificate(cert_data.encode())
        
        self._public_key = cert.public_key()
        return self._public_key

    def _rsa_encrypt(self, data: bytes) -> str:
        """Szyfrowanie RSA-OAEP SHA-256 zgodnie z wymogami KSeF 2.0."""
        public_key = self._get_public_key()
        encrypted = public_key.encrypt(
            data,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('ascii')

    def _aes_encrypt(self, data: bytes) -> bytes:
        """Szyfrowanie AES-256-CBC z paddingiem PKCS7."""
        padder = sym_padding.PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()
        cipher = Cipher(algorithms.AES(self.enc_key), modes.CBC(self.enc_iv))
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()

    # --- Zarządzanie Autoryzacją ---

    def authenticate(self):
        """Przeprowadza pełną autoryzację: Challenge -> Token -> Redeem JWT."""
        logger.info("KSeF: Start autoryzacji (NIP: %s)", self.nip)
        
        # 1. Challenge
        resp = self._request("POST", "/auth/challenge", json={
            "contextIdentifier": {"type": "nip", "value": self.nip}
        })
        if not resp.ok:
            raise KSeFError("Błąd /auth/challenge", resp.status_code, resp.text)
        
        cd = resp.json()
        challenge, timestamp = cd["challenge"], str(cd["timestampMs"])

        # 2. Encrypted Auth Token
        auth_plain = f"{self.token}|{timestamp}".encode('utf-8')
        enc_token = self._rsa_encrypt(auth_plain)

        resp = self._request("POST", "/auth/ksef-token", json={
            "challenge": challenge,
            "contextIdentifier": {"type": "nip", "value": self.nip},
            "encryptedToken": enc_token
        })
        if not resp.ok:
            raise KSeFError("Błąd /auth/ksef-token", resp.status_code, resp.text)
        
        ad = resp.json()
        temp_token, ref_no = ad["authenticationToken"]["token"], ad["referenceNumber"]

        # 3. Polling Auth Status
        for _ in range(POLLING_MAX_RETRIES):
            resp = self._request("GET", f"/auth/{ref_no}", headers={"Authorization": f"Bearer {temp_token}"})
            if resp.ok and resp.json().get("status", {}).get("code") == 200:
                break
            time.sleep(POLLING_RETRY_DELAY)
        else:
            raise KSeFError("Auth Polling Timeout")

        # 4. Redeem Access Token (JWT)
        resp = self._request("POST", "/auth/token/redeem", headers={"Authorization": f"Bearer {temp_token}"})
        if not resp.ok:
            raise KSeFError("Błąd /auth/token/redeem", resp.status_code, resp.text)
        
        self.access_token = resp.json()["accessToken"]["token"]
        logger.info("KSeF: Autoryzacja udana")

    # --- Zarządzanie Sesją Online ---

    def open_session(self):
        """Otwiera sesję interaktywną i przesyła klucz symetryczny."""
        self.enc_key, self.enc_iv = os.urandom(32), os.urandom(16)
        payload = {
            "formCode": {"systemCode": "FA (3)", "schemaVersion": "1-0E", "value": "FA"},
            "encryption": {
                "encryptedSymmetricKey": self._rsa_encrypt(self.enc_key),
                "initializationVector": base64.b64encode(self.enc_iv).decode('ascii')
            }
        }
        resp = self._request("POST", "/sessions/online", json=payload)
        if not resp.ok:
            raise KSeFError("Błąd /sessions/online", resp.status_code, resp.text)
        
        self.session_ref = resp.json()["referenceNumber"]
        logger.info("KSeF: Sesja otwarta (%s)", self.session_ref)

    def close_session(self):
        """Zamyka sesję, obsługując stan 415 (oczekiwanie na gotowość)."""
        if not self.session_ref: return

        logger.info("KSeF: Zamykanie sesji %s", self.session_ref)

        # Próbujemy zamknąć sesję do skutku (może być w stanie 415)
        # Zwiększamy liczbę prób do 20 (łącznie ok. 60 sekund)
        for attempt in range(20):
            resp = self._request("POST", f"/sessions/online/{self.session_ref}/close")
            if resp.ok:
                logger.info("KSeF: Żądanie zamknięcia sesji %s wysłane pomyślnie", self.session_ref)
                break

            # Jeśli sesja jest w 415, czekamy i ponawiamy
            if resp.status_code == 400 and "415" in resp.text:
                logger.info("KSeF: Sesja %s nadal w stanie 415, czekam przed zamknięciem (%d/20)", self.session_ref, attempt + 1)
                time.sleep(POLLING_RETRY_DELAY)
                continue

            # Inny błąd - logujemy i przerywamy (np. sesja już zamknięta)
            logger.warning("KSeF: Nieudana próba zamknięcia sesji: %s", resp.text)
            break

        # Czekamy na finalny status sesji (np. 200 lub 3xx)
        for _ in range(10):
            r = self._request("GET", f"/sessions/{self.session_ref}")
            if r.ok:
                code = r.json().get("status", {}).get("code")
                if code and code != 415:
                    break
            time.sleep(POLLING_RETRY_DELAY)

        self.session_ref = None

    def logout(self):
        """Kończy sesję autoryzacyjną w KSeF."""
        if self.access_token:
            try:
                self._request("DELETE", "/auth/sessions/current")
            except Exception:
                pass
            self.access_token = None

    # --- Operacje na Fakturach ---

    def _wait_for_session_ready(self):
        """Czeka, aż nowo otwarta sesja wyjdzie ze stanu 415 i będzie gotowa do przyjmowania faktur."""
        logger.info("KSeF: Sprawdzanie gotowości sesji %s...", self.session_ref)
        for attempt in range(POLLING_MAX_RETRIES):
            resp = self._request("GET", f"/sessions/{self.session_ref}")
            if resp.ok:
                code = resp.json().get("status", {}).get("code")
                if code == 415:
                    logger.debug("KSeF: Sesja nadal w stanie 415 (próba %d)", attempt + 1)
                else:
                    logger.info("KSeF: Sesja gotowa (status: %s)", code)
                    return True
            time.sleep(POLLING_RETRY_DELAY)
        raise KSeFError(f"Timeout: Sesja {self.session_ref} nie osiągnęła gotowości")

    def send_invoice(self, xml: bytes) -> str:
        """Szyfruje i wysyła fakturę XML, poprzedzając to sprawdzeniem gotowości sesji."""
        if not self.session_ref:
            raise KSeFError("Brak otwartej sesji")

        # Kluczowe: czekamy aż sesja będzie "Ready" zanim wyślemy cokolwiek
        self._wait_for_session_ready()

        logger.info("KSeF: Wysyłanie faktury (rozmiar: %d bajtów)", len(xml))
        
        enc_body = self._aes_encrypt(xml)
        payload_raw = self.enc_iv + enc_body  # Docs: IV || ciphertext
        
        payload = {
            "invoiceHash": base64.b64encode(hashlib.sha256(xml).digest()).decode('ascii'),
            "invoiceSize": len(xml),
            "encryptedInvoiceHash": base64.b64encode(hashlib.sha256(payload_raw).digest()).decode('ascii'),
            "encryptedInvoiceSize": len(payload_raw),
            "encryptedInvoiceContent": base64.b64encode(payload_raw).decode('ascii'),
        }

        for attempt in range(POLLING_MAX_RETRIES):
            resp = self._request("POST", f"/sessions/online/{self.session_ref}/invoices", json=payload)
            if resp.ok: return resp.json()["referenceNumber"]
            
            # Jeśli sesja nie jest jeszcze gotowa (415), ponów próbę
            if resp.status_code == 400 and "415" in resp.text:
                time.sleep(POLLING_RETRY_DELAY)
                continue
            raise KSeFError("Błąd wysyłki faktury", resp.status_code, resp.text)
        raise KSeFError("Sesja KSeF niegotowa (Timeout 415)")

    def poll_status(self, inv_ref: str) -> Tuple[str, Optional[str]]:
        """Czeka na akceptację lub odrzucenie faktury przez KSeF."""
        for _ in range(POLLING_MAX_RETRIES):
            resp = self._request("GET", f"/sessions/{self.session_ref}/invoices/{inv_ref}")
            if resp.status_code == 404:
                time.sleep(POLLING_RETRY_DELAY)
                continue
            if resp.ok:
                data = resp.json()
                code = data.get("status", {}).get("code")
                if code == 200:
                    return "accepted", data.get("ksefReferenceNumber") or data.get("ksefNumber")
                if code and int(code) >= 400 and code != 405:
                    return "rejected", data.get("processingDescription", "Odrzucona")
            time.sleep(POLLING_RETRY_DELAY)
        raise KSeFError("Timeout sprawdzania statusu faktury")


# --- XML Generator (FA(3)) ---

def build_fa3_xml(invoice, is_correction: bool = False) -> bytes:
    """Generuje XML faktury w standardzie FA(3)."""
    seller = settings.INVOICE_SELLER_DATA
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    ET.register_namespace('', FA3_NS)
    q = lambda n: f'{{{FA3_NS}}}{n}'
    root = ET.Element(q('Faktura'), xmlns=FA3_NS)
    
    # Nagłówek
    nagl = ET.SubElement(root, q('Naglowek'))
    ET.SubElement(nagl, q('KodFormularza'), kodSystemowy="FA (3)", wersjaSchemy="1-0E").text = "FA"
    ET.SubElement(nagl, q('WariantFormularza')).text = "3"
    ET.SubElement(nagl, q('DataWytworzeniaFa')).text = now_str
    ET.SubElement(nagl, q('SystemInfo')).text = "wyznaczresurs.pl v2.2"

    # Sprzedawca (Podmiot1)
    p1 = ET.SubElement(root, q('Podmiot1'))
    ds1 = ET.SubElement(p1, q('DaneIdentyfikacyjne'))
    ET.SubElement(ds1, q('NIP')).text = seller['nip'].replace('-', '')
    ET.SubElement(ds1, q('PelnaNazwa')).text = seller['name']
    ET.SubElement(ET.SubElement(p1, q('Adres')), q('AdresL1')).text = seller['address']

    # Nabywca (Podmiot2)
    p2 = ET.SubElement(root, q('Podmiot2'))
    ds2 = ET.SubElement(p2, q('DaneIdentyfikacyjne'))
    if invoice.buyer_nip: ET.SubElement(ds2, q('NIP')).text = invoice.buyer_nip.replace('-', '')
    ET.SubElement(ds2, q('PelnaNazwa')).text = invoice.buyer_name or 'Osoba prywatna'
    if invoice.buyer_address: ET.SubElement(ET.SubElement(p2, q('Adres')), q('AdresL1')).text = invoice.buyer_address

    # Dane faktury
    fa = ET.SubElement(root, q('Fa'))
    ET.SubElement(fa, q('KodWaluty')).text = 'PLN'
    ET.SubElement(fa, q('P_1')).text = invoice.issue_date.strftime('%Y-%m-%d')
    ET.SubElement(fa, q('P_2')).text = invoice.invoice_number
    ET.SubElement(fa, q('P_6')).text = invoice.issue_date.strftime('%Y-%m-%d')
    ET.SubElement(fa, q('RodzajFaktury')).text = 'KOR' if is_correction else 'VAT'

    if is_correction and invoice.corrected_invoice:
        k_fa = ET.SubElement(fa, q('DaneFaKorygowanej'))
        ET.SubElement(k_fa, q('DataWystFaKorygowanej')).text = invoice.corrected_invoice.issue_date.strftime('%Y-%m-%d')
        ET.SubElement(k_fa, q('NrFaKorygowanej')).text = invoice.corrected_invoice.invoice_number
        if invoice.corrected_invoice.ksef_reference_number: ET.SubElement(k_fa, q('NrKSeFFaKorygowanej')).text = invoice.corrected_invoice.ksef_reference_number
        if invoice.correction_reason: ET.SubElement(fa, q('PrzyczynaKorekty')).text = invoice.correction_reason

    # Pozycje
    w = ET.SubElement(fa, q('FaWiersz'))
    ET.SubElement(w, q('NrWierszaFa')).text = '1'
    ET.SubElement(w, q('P_7')).text = invoice.service_name
    for t, v in [('P_8A', 'szt'), ('P_8B', '1'), ('P_9A', f"{invoice.net_amount:.2f}"), ('P_11', f"{invoice.net_amount:.2f}"), ('P_12', '23')]:
        ET.SubElement(w, q(t)).text = v

    # Podsumowanie i VAT
    ET.SubElement(fa, q('P_13_1')).text = f"{invoice.net_amount:.2f}"
    ET.SubElement(fa, q('P_14_1')).text = f"{invoice.vat_amount:.2f}"
    ET.SubElement(fa, q('P_15')).text    = f"{invoice.gross_amount:.2f}"

    adn = ET.SubElement(fa, q('Adnotacje'))
    for p in ['P_16', 'P_17', 'P_18', 'P_19']: ET.SubElement(adn, q(p)).text = '2'

    if invoice.payment_terms != 'paid':
        platn = ET.SubElement(fa, q('Platnosc'))
        ET.SubElement(platn, q('Zaplacono')).text = '0'
        ET.SubElement(ET.SubElement(platn, q('TerminPlatnosci')), q('Termin')).text = invoice.issue_date.strftime('%Y-%m-%d')
        ET.SubElement(ET.SubElement(platn, q('RachunekBankowy')), q('NrRB')).text = seller['bank_account'].replace(' ', '')

    ET.SubElement(root, q('Stopka')).text = ' '
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


# --- API ---

def submit_to_ksef(invoice, is_correction: bool = False):
    client = KSeFClient()
    invoice.ksef_status = "sent"
    invoice.save(update_fields=["ksef_status"])
    try:
        client.authenticate()
        xml = build_fa3_xml(invoice, is_correction)
        client.open_session()
        inv_ref = client.send_invoice(xml)
        
        # Kluczowa zmiana: najpierw czekamy na status faktury, 
        # co naturalnie "odczeka" czas procesowania w sesji (stan 415).
        status, result = client.poll_status(inv_ref)
        
        # Dopiero po zakończeniu procesowania faktury zamykamy sesję.
        client.close_session()
        
        if status == "accepted":
            invoice.ksef_status, invoice.ksef_reference_number = "accepted", result
            invoice.save(update_fields=["ksef_status", "ksef_reference_number"])
            if not is_correction:
                invoice.user.premium += invoice.points_added
                invoice.user.save(update_fields=["premium"])
        else:
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
            raise RuntimeError(f"KSeF rejected: {result}")
    except Exception as e:
        logger.exception("KSeF Error (%s): %s", invoice.invoice_number, e)
        if invoice.ksef_status == "sent":
            invoice.ksef_status = "rejected"
            invoice.save(update_fields=["ksef_status"])
        raise
    finally:
        try: client.logout()
        except: pass

def submit(invoice): submit_to_ksef(invoice, is_correction=False)
def submit_correction(invoice): submit_to_ksef(invoice, is_correction=True)
