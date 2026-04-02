"""
Serwis KSeF (Krajowy System e-Faktur) — Integracja z API 2.0 (FA(3)).
Zgodny z wymogami obowiązującymi od 2026 r.
Obsługuje pełny format tokena: Identyfikator|NIP|Klucz.
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
    Zapewnia autentykację JWT przy użyciu tokena w formacie Identyfikator|NIP|Klucz.
    """

    def __init__(self):
        self.base_url = settings.KSEF_API_URL.rstrip('/')
        self.nip = settings.KSEF_NIP.replace('-', '').strip()
        
        # Parsowanie tokena (zawsze używamy NIP jako identyfikatora, a z .env bierzemy tylko klucz)
        full_token = settings.KSEF_TOKEN.strip()
        # Omijamy dzielenie, ponieważ pełny token z pipe może być wymagany
        self.token = full_token

        # Identyfikator kontekstu dla sesji interaktywnej to zawsze NIP
        self.context_id = self.nip
        self.context_type = "nip"

        self.session = requests.Session()
        self.access_token = None
        self.session_ref = None
        self.enc_key = None
        self.enc_iv = None
        self._public_key = None

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Wykonywanie zapytań HTTP do API KSeF z rozszerzoną diagnostyką."""
        url = f"{self.base_url}{path}"
        headers = kwargs.get('headers', {}).copy()
        headers.setdefault('Accept', 'application/json')
        
        if method in ['POST', 'PUT']:
            headers.setdefault('Content-Type', 'application/json')
        
        if self.access_token:
            headers.setdefault('Authorization', f"Bearer {self.access_token}")
        
        kwargs['headers'] = headers
        
        logger.info("KSeF API Request: %s %s", method, url)
        try:
            # Zwiększamy timeout do 60s na produkcji
            start_time = time.time()
            resp = self.session.request(method, url, timeout=60, **kwargs)
            duration = time.time() - start_time
            
            logger.info("KSeF API Response: %d (%s) w %.2fs", resp.status_code, method, duration)
            
            if not resp.ok:
                logger.warning("KSeF API Error Body: %s", resp.text[:1000])
            return resp
        except requests.RequestException as e:
            logger.error("KSeF Connection Failed (%s %s): %s", method, url, e)
            raise KSeFError(f"Błąd połączenia z API KSeF: {e}")

    # --- Szyfrowanie (RSA i AES) ---

    def _get_public_key(self, usage_type='kseftokenencryption'):
        """Pobiera i cache'uje klucz publiczny MF do szyfrowania."""
        attr_name = f'_public_key_{usage_type}'
        if getattr(self, attr_name, None):
            return getattr(self, attr_name)

        resp = self._request("GET", "/security/public-key-certificates")
        if not resp.ok:
            raise KSeFError("Błąd pobierania certyfikatów MF", resp.status_code, resp.text)
        
        certs = resp.json()
        cert_data = next((c.get('certificate') for c in certs if usage_type.lower() in str(c.get('usage', '')).lower()), certs[0].get('certificate'))

        try:
            cert_bytes = base64.b64decode(cert_data)
            cert = load_der_x509_certificate(cert_bytes)
        except Exception:
            cert = load_pem_x509_certificate(cert_data.encode())
        
        pub_key = cert.public_key()
        setattr(self, attr_name, pub_key)
        return pub_key

    def _rsa_encrypt(self, data: bytes, usage_type='kseftokenencryption') -> str:
        """Szyfrowanie RSA-OAEP SHA-256 zgodnie z wymogami KSeF 2.0."""
        public_key = self._get_public_key(usage_type)
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
        logger.info("KSeF: Start autoryzacji (%s: %s)", self.context_type, self.context_id)
        
        # Pobieramy certyfikat MF WCZEŚNIEJ, aby nie tracić czasu podczas trwania challenge
        self._get_public_key()

        # 1. Challenge
        resp = self._request("POST", "/auth/challenge", json={
            "contextIdentifier": {"type": self.context_type, "value": self.context_id}
        })
        if not resp.ok:
            raise KSeFError("Błąd /auth/challenge", resp.status_code, resp.text)
        
        cd = resp.json()
        challenge = cd["challenge"]
        
        # Logujemy dostępne pola czasu dla diagnostyki (bez wartości challenge)
        logger.info("KSeF Challenge Info: timestamp=%s, timestampMs=%s", cd.get("timestamp"), cd.get("timestampMs"))
        
        # Próbujemy użyć timestampMs jako pierwszego wyboru, jeśli brak - timestamp (ISO)
        # W v2 MF często preferuje wartość tekstową z pola timestamp do połączenia z tokenem
        ts_value = str(cd.get("timestampMs") or cd.get("timestamp"))

        # 2. Encrypted Auth Token
        # Format: Token|Timestamp
        auth_plain = f"{self.token}|{ts_value}".encode('utf-8')
        enc_token = self._rsa_encrypt(auth_plain)

        resp = self._request("POST", "/auth/ksef-token", json={
            "challenge": challenge,
            "contextIdentifier": {"type": self.context_type, "value": self.context_id},
            "encryptedToken": enc_token
        })
        if not resp.ok:
            raise KSeFError("Błąd /auth/ksef-token", resp.status_code, resp.text)
        
        ad = resp.json()
        temp_token, ref_no = ad["authenticationToken"]["token"], ad["referenceNumber"]

        # 3. Polling Auth Status
        logger.info("KSeF: Oczekiwanie na potwierdzenie autoryzacji (ref: %s)...", ref_no)
        for attempt in range(POLLING_MAX_RETRIES):
            resp = self._request("GET", f"/auth/{ref_no}", headers={"Authorization": f"Bearer {temp_token}"})
            if resp.ok:
                data = resp.json()
                status_code = data.get("status", {}).get("code")
                logger.info("KSeF Auth Polling [%d/%d]: Status JSON = %s", attempt + 1, POLLING_MAX_RETRIES, status_code)
                
                if status_code == 200:
                    break
                if status_code and int(status_code) >= 400:
                    raise KSeFError(f"Błąd autoryzacji (JSON): {status_code}", resp.status_code, resp.text)
            
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
                "encryptedSymmetricKey": self._rsa_encrypt(self.enc_key, usage_type='symmetrickeyencryption'),
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

        for attempt in range(20):
            resp = self._request("POST", f"/sessions/online/{self.session_ref}/close")
            if resp.ok:
                logger.info("KSeF: Sesja %s zamknięta", self.session_ref)
                break
            if resp.status_code == 400 and "415" in resp.text:
                time.sleep(POLLING_RETRY_DELAY)
                continue
            break
        
        self.session_ref = None

    def logout(self):
        """Kończy sesję autoryzacyjną w KSeF."""
        if self.access_token:
            try:
                self._request("DELETE", "/auth/sessions/current")
            except:
                pass
            self.access_token = None

    # --- Operacje na Fakturach ---

    def _wait_for_session_ready(self):
        """Czeka, aż nowo otwarta sesja osiągnie status 100 (Gotowa/Otwarta)."""
        logger.info("KSeF: Sprawdzanie gotowości sesji %s...", self.session_ref)
        for attempt in range(POLLING_MAX_RETRIES):
            resp = self._request("GET", f"/sessions/{self.session_ref}")
            if resp.ok:
                code = resp.json().get("status", {}).get("code")
                if code is not None and int(code) in (100, 200):
                    logger.info("KSeF: Sesja gotowa (status: %s)", code)
                    return True
                logger.info("KSeF: Sesja %s w stanie %s (próba %d/%d)", self.session_ref, code, attempt + 1, POLLING_MAX_RETRIES)
            time.sleep(POLLING_RETRY_DELAY)
        raise KSeFError(f"Timeout: Sesja {self.session_ref} nie osiągnęła statusu 200")

    def send_invoice(self, xml: bytes) -> str:
        """Szyfruje i wysyła fakturę XML."""
        if not self.session_ref:
            raise KSeFError("Brak otwartej sesji")

        self._wait_for_session_ready()

        logger.info("KSeF: Przygotowanie payloadu (rozmiar XML: %d bajtów)", len(xml))
        enc_body = self._aes_encrypt(xml)
        
        payload = {
            "invoiceHash": base64.b64encode(hashlib.sha256(xml).digest()).decode('ascii'),
            "invoiceSize": len(xml),
            "encryptedInvoiceHash": base64.b64encode(hashlib.sha256(enc_body).digest()).decode('ascii'),
            "encryptedInvoiceSize": len(enc_body),
            "encryptedInvoiceContent": base64.b64encode(enc_body).decode('ascii')
        }

        logger.info("KSeF: Wysyłanie faktury do sesji %s...", self.session_ref)
        for attempt in range(POLLING_MAX_RETRIES):
            resp = self._request("POST", f"/sessions/online/{self.session_ref}/invoices", json=payload)
            if resp.ok:
                inv_ref = resp.json().get("invoiceReferenceNumber") or resp.json().get("referenceNumber")
                logger.info("KSeF: Faktura wysłana. Ref: %s", inv_ref)
                return inv_ref
            
            if resp.status_code == 400 and "415" in resp.text:
                time.sleep(POLLING_RETRY_DELAY)
                continue
            
            logger.error("KSeF send_invoice failed %d: %s", resp.status_code, resp.text)
            raise KSeFError(f"Błąd wysyłki faktury ({resp.status_code})", resp.status_code, resp.text)
        
        raise KSeFError("Sesja KSeF niegotowa do wysyłki (Timeout 415)")

    def poll_status(self, inv_ref: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Czeka na akceptację faktury."""
        logger.info("KSeF: Sprawdzanie statusu faktury %s", inv_ref)
        for attempt in range(POLLING_MAX_RETRIES):
            resp = self._request("GET", f"/sessions/{self.session_ref}/invoices/{inv_ref}")
            if resp.status_code == 404:
                time.sleep(POLLING_RETRY_DELAY)
                continue
            if resp.ok:
                data = resp.json()
                code = data.get("status", {}).get("code")
                logger.info("KSeF poll_status [%d/%d]: Status code = %s", attempt + 1, POLLING_MAX_RETRIES, code)
                if code == 200:
                    ksef_no = data.get("ksefReferenceNumber") or data.get("ksefNumber")
                    inv_hash = data.get("invoiceHash")
                    return "accepted", ksef_no, inv_hash
                if code and int(code) >= 400 and code != 405:
                    return "rejected", data.get("processingDescription", "Odrzucona"), None
            time.sleep(POLLING_RETRY_DELAY)
        raise KSeFError("Timeout statusu faktury")


# --- XML Generator (FA(3)) ---

def build_fa3_xml(invoice, is_correction: bool = False) -> bytes:
    """Generuje XML faktury w standardzie FA(3)."""
    seller = settings.INVOICE_SELLER_DATA
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    ET.register_namespace('', FA3_NS)
    q = lambda n: f'{{{FA3_NS}}}{n}'
    
    root = ET.Element(q('Faktura'))
    
    # Nagłówek
    nagl = ET.SubElement(root, q('Naglowek'))
    ET.SubElement(nagl, q('KodFormularza'), kodSystemowy="FA (3)", wersjaSchemy="1-0E").text = "FA"
    ET.SubElement(nagl, q('WariantFormularza')).text = "3"
    ET.SubElement(nagl, q('DataWytworzeniaFa')).text = now_str

    # Sprzedawca (Podmiot1)
    p1 = ET.SubElement(root, q('Podmiot1'))
    ds1 = ET.SubElement(p1, q('DaneIdentyfikacyjne'))
    ET.SubElement(ds1, q('NIP')).text = seller['nip'].replace('-', '')
    ET.SubElement(ds1, q('Nazwa')).text = seller['name']
    
    adr1 = ET.SubElement(p1, q('Adres'))
    ET.SubElement(adr1, q('KodKraju')).text = 'PL'
    ET.SubElement(adr1, q('AdresL1')).text = seller['address']

    # Nabywca (Podmiot2)
    p2 = ET.SubElement(root, q('Podmiot2'))
    ds2 = ET.SubElement(p2, q('DaneIdentyfikacyjne'))
    if invoice.buyer_nip:
        ET.SubElement(ds2, q('NIP')).text = invoice.buyer_nip.replace('-', '')
    else:
        ET.SubElement(ds2, q('BrakID')).text = '1'
        
    ET.SubElement(ds2, q('Nazwa')).text = invoice.buyer_name or 'Osoba prywatna'
    
    if invoice.buyer_address:
        adr2 = ET.SubElement(p2, q('Adres'))
        ET.SubElement(adr2, q('KodKraju')).text = 'PL'
        ET.SubElement(adr2, q('AdresL1')).text = invoice.buyer_address

    ET.SubElement(p2, q('JST')).text = '2'
    ET.SubElement(p2, q('GV')).text = '2'

    # Dane faktury
    fa = ET.SubElement(root, q('Fa'))
    ET.SubElement(fa, q('KodWaluty')).text = 'PLN'
    ET.SubElement(fa, q('P_1')).text = invoice.issue_date.strftime('%Y-%m-%d')
    ET.SubElement(fa, q('P_2')).text = invoice.invoice_number
    ET.SubElement(fa, q('P_6')).text = invoice.issue_date.strftime('%Y-%m-%d')

    # Podsumowanie i VAT
    ET.SubElement(fa, q('P_13_1')).text = f"{invoice.net_amount:.2f}"
    ET.SubElement(fa, q('P_14_1')).text = f"{invoice.vat_amount:.2f}"
    ET.SubElement(fa, q('P_15')).text    = f"{invoice.gross_amount:.2f}"

    # Adnotacje (FA(3))
    adn = ET.SubElement(fa, q('Adnotacje'))
    for p in ['P_16', 'P_17', 'P_18', 'P_18A']:
        ET.SubElement(adn, q(p)).text = '2'
        
    zw = ET.SubElement(adn, q('Zwolnienie'))
    ET.SubElement(zw, q('P_19N')).text = '1'
    
    nst = ET.SubElement(adn, q('NoweSrodkiTransportu'))
    ET.SubElement(nst, q('P_22N')).text = '1'
    
    ET.SubElement(adn, q('P_23')).text = '2'
    
    pm = ET.SubElement(adn, q('PMarzy'))
    ET.SubElement(pm, q('P_PMarzyN')).text = '1'

    ET.SubElement(fa, q('RodzajFaktury')).text = 'KOR' if is_correction else 'VAT'

    if is_correction and invoice.corrected_invoice:
        k_fa = ET.SubElement(fa, q('DaneFaKorygowanej'))
        ET.SubElement(k_fa, q('DataWystFaKorygowanej')).text = invoice.corrected_invoice.issue_date.strftime('%Y-%m-%d')
        ET.SubElement(k_fa, q('NrFaKorygowanej')).text = invoice.corrected_invoice.invoice_number
        if invoice.corrected_invoice.ksef_reference_number:
            ET.SubElement(k_fa, q('NrKSeF')).text = invoice.corrected_invoice.ksef_reference_number
        else:
            ET.SubElement(k_fa, q('NrKSeFN')).text = '1'
        
        if invoice.correction_reason:
            ET.SubElement(fa, q('PrzyczynaKorekty')).text = invoice.correction_reason

    # Pozycje
    w = ET.SubElement(fa, q('FaWiersz'))
    ET.SubElement(w, q('NrWierszaFa')).text = '1'
    ET.SubElement(w, q('P_7')).text = invoice.service_name
    for t, v in [('P_8A', 'szt'), ('P_8B', '1'), ('P_9A', f"{invoice.net_amount:.2f}"), ('P_11', f"{invoice.net_amount:.2f}"), ('P_12', '23')]:
        ET.SubElement(w, q(t)).text = v

    if invoice.payment_terms != 'paid':
        platn = ET.SubElement(fa, q('Platnosc'))
        ET.SubElement(platn, q('Zaplacono')).text = '0'
        ET.SubElement(ET.SubElement(platn, q('TerminPlatnosci')), q('Termin')).text = invoice.issue_date.strftime('%Y-%m-%d')
        ET.SubElement(ET.SubElement(platn, q('RachunekBankowy')), q('NrRB')).text = seller['bank_account'].replace(' ', '')

    xml_content = ET.tostring(root, encoding='utf-8')
    xml_declaration = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    return xml_declaration + xml_content


# --- API ---

def submit_to_ksef(invoice, is_correction: bool = False):
    client = KSeFClient()
    invoice.ksef_status = "sent"
    invoice.save(update_fields=["ksef_status"])
    try:
        client.authenticate()
        xml = build_fa3_xml(invoice, is_correction)
        logger.info("KSeF: Wygenerowano XML FA(3).")
        client.open_session()
        inv_ref = client.send_invoice(xml)
        status, result, inv_hash = client.poll_status(inv_ref)
        client.close_session()

        if status == "accepted":
            invoice.ksef_status = "accepted"
            invoice.ksef_reference_number = result
            invoice.ksef_invoice_hash = inv_hash
            invoice.save(update_fields=["ksef_status", "ksef_reference_number", "ksef_invoice_hash"])
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

def refresh_ksef_qr(invoice):
    """
    Dla starszych faktur, które nie mają hasha w bazie (lub został zgubiony).
    Generuje XML z obecnego stanu faktury, oblicza jego skrót i zapisuje.
    (Skrót może minimalnie odbiegać od oryginalnego przez zmieniającą się datę wygenerowania XML).
    """
    if not invoice.ksef_reference_number:
        raise ValueError("Faktura nie posiada numeru KSeF.")
    xml = build_fa3_xml(invoice, invoice.is_correction)
    inv_hash = base64.b64encode(hashlib.sha256(xml).digest()).decode('ascii')
    invoice.ksef_invoice_hash = inv_hash
    invoice.save(update_fields=["ksef_invoice_hash"])
