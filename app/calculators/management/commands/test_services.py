"""
Komenda diagnostyczna — testuje połączenie SMTP (email) i KSeF API krok po kroku.

Użycie:
    python manage.py test_services           # testuje oba
    python manage.py test_services --email   # tylko email
    python manage.py test_services --ksef    # tylko KSeF
    python manage.py test_services --email --to admin@example.com  # wyślij testowy mail
"""
import base64
import hashlib
import smtplib
import socket
import ssl
import sys
from django.conf import settings
from django.core.management.base import BaseCommand
import requests


class Command(BaseCommand):
    help = 'Diagnostyka: testuje połączenie SMTP i KSeF API'

    def add_arguments(self, parser):
        parser.add_argument('--email', action='store_true', help='Testuj tylko email')
        parser.add_argument('--ksef',  action='store_true', help='Testuj tylko KSeF')
        parser.add_argument('--to',    type=str, default='', help='Adres docelowy testu email')

    def handle(self, *args, **options):
        run_email = options['email'] or not options['ksef']
        run_ksef  = options['ksef']  or not options['email']

        if run_email:
            self._test_email(options.get('to') or '')
        if run_ksef:
            self._test_ksef()

    # ─────────────────────────────────────────────────────────────────────
    # EMAIL
    # ─────────────────────────────────────────────────────────────────────

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f'  [OK] {msg}'))

    def _err(self, msg):
        self.stdout.write(self.style.ERROR(f'  [!!] {msg}'))

    def _info(self, msg):
        self.stdout.write(f'  [..] {msg}')

    def _test_email(self, send_to: str = ''):
        self.stdout.write('\n=== TEST EMAIL (SMTP) ===')
        host   = settings.EMAIL_HOST
        port   = settings.EMAIL_PORT
        use_ssl = settings.EMAIL_USE_SSL
        use_tls = settings.EMAIL_USE_TLS
        user   = settings.EMAIL_HOST_USER
        passwd = settings.EMAIL_HOST_PASSWORD
        backend = settings.EMAIL_BACKEND

        self._info(f'Backend:  {backend}')
        self._info(f'Host:     {host}:{port}')
        self._info(f'SSL={use_ssl}  TLS(STARTTLS)={use_tls}')
        self._info(f'User:     {user}')
        self._info(f'Password: {"[ustawione]" if passwd else "[BRAK!]"}')

        if 'console' in backend:
            self._err('Backend to console — emaile nie są wysyłane! '
                      'Ustaw DEBUG=False w .env aby używać SMTP.')
            return

        if not host or host == 'localhost':
            self._err(f'EMAIL_HOST={host!r} — nieprawidłowy host SMTP.')
            return

        if use_ssl and use_tls:
            self._err('Nie można jednocześnie EMAIL_USE_SSL=True i EMAIL_USE_TLS=True.')
            return

        # Krok 1: DNS/socket
        self._info(f'Krok 1: Sprawdzam DNS/port {host}:{port}...')
        try:
            ip = socket.gethostbyname(host)
            self._ok(f'DNS: {host} → {ip}')
        except socket.gaierror as e:
            self._err(f'DNS resolution failed: {e}')
            return

        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            self._ok(f'TCP: port {port} otwarty')
        except (ConnectionRefusedError, OSError) as e:
            self._err(f'TCP connection failed: {e}')
            self._info('Sprawdz firewall/VPN lub zmien port w .env')
            return

        # Krok 2: Handshake SMTP
        self._info(f'Krok 2: Nawiazuję sesję SMTP...')
        try:
            if use_ssl:
                context = ssl.create_default_context()
                smtp = smtplib.SMTP_SSL(host, port, context=context, timeout=10)
            else:
                smtp = smtplib.SMTP(host, port, timeout=10)
                if use_tls:
                    smtp.starttls(context=ssl.create_default_context())

            self._ok(f'Połączono ({"SSL" if use_ssl else "STARTTLS" if use_tls else "PLAIN"})')

            # Krok 3: Logowanie
            self._info('Krok 3: Logowanie...')
            if user and passwd:
                smtp.login(user, passwd)
                self._ok(f'Zalogowano jako {user}')
            else:
                self._err('Brak USER lub PASSWORD — nie można się zalogować')
                smtp.quit()
                return

            # Krok 4: Wysyłka testowego emaila (opcjonalna)
            if send_to:
                self._info(f'Krok 4: Wysyłam testowy email do {send_to}...')
                from django.core.mail import send_mail
                sent = send_mail(
                    subject='[wyznaczresurs] Test SMTP',
                    message='Ten email to test konfiguracji SMTP.\n\nJeśli go widzisz — działa!',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[send_to],
                    fail_silently=False,
                )
                self._ok(f'Email wysłany ({sent} wiadomość/i)')
            else:
                self._info('Krok 4: (pomiń wysyłkę — dodaj --to adres@email.pl)')

            smtp.quit()
            self._ok('Sesja SMTP zamknięta')

        except smtplib.SMTPAuthenticationError as e:
            self._err(f'Błąd logowania SMTP: {e}')
            self._info('Sprawdz EMAIL_HOST_USER i EMAIL_HOST_PASSWORD w .env')
        except smtplib.SMTPConnectError as e:
            self._err(f'Błąd połączenia SMTP: {e}')
        except ssl.SSLError as e:
            self._err(f'Błąd SSL: {e}')
            if not use_ssl and port == 465:
                self._info('Port 465 wymaga SSL. Ustaw EMAIL_USE_SSL=True w .env')
            if use_ssl and port == 587:
                self._info('Port 587 wymaga STARTTLS. Ustaw EMAIL_USE_TLS=True i EMAIL_USE_SSL=False')
        except Exception as e:
            self._err(f'Nieoczekiwany błąd: {type(e).__name__}: {e}')

    # ─────────────────────────────────────────────────────────────────────
    # KSEF
    # ─────────────────────────────────────────────────────────────────────

    def _test_ksef(self):
        self.stdout.write('\n=== TEST KSEF API ===')
        nip    = settings.KSEF_NIP
        token  = settings.KSEF_TOKEN
        api    = settings.KSEF_API_URL
        sandbox = settings.KSEF_SANDBOX

        self._info(f'URL:     {api}')
        self._info(f'Sandbox: {sandbox}')
        self._info(f'NIP:     {nip}')
        self._info(f'Token:   {token[:30]}...' if token else 'Token: [BRAK!]')

        # Analiza formatu tokenu
        self._info('Krok 1: Analiza formatu tokenu...')
        if not token:
            self._err('KSEF_TOKEN nie jest ustawiony w .env')
            return
        if not nip or not nip.isdigit() or len(nip) != 10:
            self._err(f'KSEF_NIP={nip!r} — powinien mieć 10 cyfr')
            return

        parts = token.split('|')
        if len(parts) == 3:
            self._ok(f'Format tokenu: 3-częściowy (data|nip|hash) — wygląda poprawnie')
            self._info(f'  Data:  {parts[0]}')
            self._info(f'  NIP:   {parts[1]}')
            self._info(f'  Hash:  {parts[2][:20]}...')
            if parts[1] != f'nip-{nip}':
                self._err(f'NIP w tokenie ({parts[1]}) != KSEF_NIP (nip-{nip})')
        else:
            self._info(f'Format tokenu: niestandardowy ({len(parts)} części) — używam całego stringa')

        # Krok 2: DNS/TCP
        self._info('Krok 2: Sprawdzam dostępność KSeF API...')
        from urllib.parse import urlparse
        parsed = urlparse(api)
        host = parsed.hostname
        port = parsed.port or 443
        try:
            ip = socket.gethostbyname(host)
            self._ok(f'DNS: {host} → {ip}')
        except socket.gaierror as e:
            self._err(f'DNS failed: {e}')
            return

        # Krok 3: AuthorisationChallenge
        self._info('Krok 3: POST /api/online/Session/AuthorisationChallenge...')
        try:
            resp = requests.post(
                f'{api}/api/online/Session/AuthorisationChallenge',
                json={'contextIdentifier': {'type': 'onip', 'identifier': nip}},
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=15,
            )
            self._info(f'  HTTP: {resp.status_code}')
            if not resp.ok:
                self._err(f'Błąd: {resp.text[:300]}')
                return

            data = resp.json()
            challenge_hex = data.get('challenge', '')
            timestamp     = data.get('timestamp', '')
            self._ok(f'Challenge: {challenge_hex[:20]}... | timestamp: {timestamp}')

        except requests.Timeout:
            self._err('Timeout — KSeF nie odpowiada (>15s)')
            return
        except requests.ConnectionError as e:
            self._err(f'Connection error: {e}')
            return

        # Krok 4: Oblicz token hash
        self._info('Krok 4: Obliczam hash tokenu...')
        try:
            challenge_bytes = bytes.fromhex(challenge_hex)
            self._ok(f'Challenge zdekodowany ({len(challenge_bytes)} bajtów)')
        except ValueError:
            self._info('Challenge nie jest HEX — używam UTF-8')
            challenge_bytes = challenge_hex.encode('utf-8')

        token_bytes = token.encode('utf-8')
        hash_val    = hashlib.sha256(challenge_bytes + token_bytes).digest()
        token_b64   = base64.b64encode(hash_val).decode('ascii')
        self._ok(f'SHA-256 hash: {token_b64[:30]}...')

        # Krok 5: InitialisationToken
        self._info('Krok 5: POST /api/online/Session/InitialisationToken...')
        try:
            resp2 = requests.post(
                f'{api}/api/online/Session/InitialisationToken',
                json={
                    'contextIdentifier': {'type': 'onip', 'identifier': nip},
                    'credentialIdentifier': None,
                    'token': token_b64,
                },
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                timeout=15,
            )
            self._info(f'  HTTP: {resp2.status_code}')
            if not resp2.ok:
                self._err(f'Błąd autoryzacji: {resp2.text[:400]}')
                self._info('Mozliwe przyczyny:')
                self._info('  - Token wygasl (tokeny sa wazne ~30 dni)')
                self._info('  - Token nie jest aktywny dla tego NIP')
                self._info('  - Zly format hash (sprawdz algorytm)')
                return

            session_data = resp2.json()
            session_token = (session_data.get('sessionToken') or {}).get('token', '')
            self._ok(f'Sesja zainicjowana! token={session_token[:20]}...')

        except Exception as e:
            self._err(f'Błąd: {type(e).__name__}: {e}')
            return

        # Krok 6: Zamknij sesję
        self._info('Krok 6: Zamykam sesję...')
        try:
            requests.get(
                f'{api}/api/online/Session/Terminate',
                headers={'X-Session-Token': session_token, 'Accept': 'application/json'},
                timeout=10,
            )
            self._ok('Sesja zamknięta')
        except Exception:
            pass

        self._ok('KSeF: WSZYSTKIE KROKI ZAKONCZONE POMYSLNIE')
        self.stdout.write(self.style.SUCCESS('\nToken jest prawidlowy i polaczenie dziala!'))
