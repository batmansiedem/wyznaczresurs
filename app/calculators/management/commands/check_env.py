"""
Komenda diagnostyczna: sprawdza czy wszystkie wymagane zmienne środowiskowe
są poprawnie ustawione przed uruchomieniem produkcyjnym.

Użycie:
    python manage.py check_env
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os


PLACEHOLDER_PATTERNS = [
    "TWOJ_", "ZMIEN_", "WPISZ_", "YOUR_", "CHANGE_", "TODO", "EXAMPLE",
    "django-insecure",
]

INSECURE_SECRET_KEY = 'django-insecure-gcgc_@q^ulas&@sl)gk86v8(wc#e0q6*wvbkb06o(t)ftx$(r2'


def _is_placeholder(value: str) -> bool:
    if not value:
        return False
    val_upper = value.upper()
    return any(pat.upper() in val_upper for pat in PLACEHOLDER_PATTERNS)


class Command(BaseCommand):
    help = 'Sprawdza poprawność zmiennych środowiskowych (.env)'

    def handle(self, *args, **options):
        ok = True

        def check(label: str, condition: bool, hint: str = ''):
            nonlocal ok
            if condition:
                self.stdout.write(self.style.SUCCESS(f'  [OK]  {label}'))
            else:
                self.stdout.write(self.style.ERROR(f'  [!!]  {label}'))
                if hint:
                    self.stdout.write(f'         -> {hint}')
                ok = False

        self.stdout.write('\n=== DJANGO ===')
        check(
            'SECRET_KEY jest ustawiony i nie jest domyślny',
            bool(settings.SECRET_KEY)
            and settings.SECRET_KEY != INSECURE_SECRET_KEY
            and not _is_placeholder(settings.SECRET_KEY),
            'Wygeneruj nowy klucz: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
        )
        check(
            f'DEBUG={settings.DEBUG} (na produkcji powinno być False)',
            not settings.DEBUG,
            'Ustaw DEBUG=False w .env',
        )
        check(
            f'ALLOWED_HOSTS={settings.ALLOWED_HOSTS}',
            'localhost' not in settings.ALLOWED_HOSTS or len(settings.ALLOWED_HOSTS) > 1,
            'Dodaj domenę produkcyjną do ALLOWED_HOSTS w .env',
        )

        self.stdout.write('\n=== E-MAIL (SMTP) ===')
        check(
            f'EMAIL_HOST={settings.EMAIL_HOST}',
            bool(settings.EMAIL_HOST) and settings.EMAIL_HOST != 'localhost',
            'Ustaw EMAIL_HOST na serwer SMTP (np. hostinger.com)',
        )
        check(
            'EMAIL_HOST_USER jest ustawiony',
            bool(settings.EMAIL_HOST_USER),
            'Ustaw EMAIL_HOST_USER w .env',
        )
        check(
            'EMAIL_HOST_PASSWORD jest ustawiony',
            bool(settings.EMAIL_HOST_PASSWORD),
            'Ustaw EMAIL_HOST_PASSWORD w .env',
        )
        check(
            f'EMAIL_BACKEND={settings.EMAIL_BACKEND}',
            'smtp' in settings.EMAIL_BACKEND.lower(),
            'Na produkcji EMAIL_BACKEND musi być smtp (DEBUG=False aktywuje smtp automatycznie)',
        )

        self.stdout.write('\n=== PAYPAL ===')
        client_id = settings.PAYPAL_CLIENT_ID
        client_secret = settings.PAYPAL_CLIENT_SECRET
        check(
            f'PAYPAL_SANDBOX={settings.PAYPAL_SANDBOX}',
            True,  # Zawsze OK — tylko informacja
        )
        check(
            'PAYPAL_CLIENT_ID jest ustawiony (nie placeholder)',
            bool(client_id) and not _is_placeholder(client_id),
            'Utwórz aplikację na developer.paypal.com i wpisz Client ID do .env',
        )
        check(
            'PAYPAL_CLIENT_SECRET jest ustawiony (nie placeholder)',
            bool(client_secret) and not _is_placeholder(client_secret),
            'Wpisz PayPal Secret do .env',
        )

        self.stdout.write('\n=== KSEF ===')
        ksef_token = settings.KSEF_TOKEN
        ksef_nip = settings.KSEF_NIP
        check(
            f'KSEF_SANDBOX={settings.KSEF_SANDBOX} | API URL: {settings.KSEF_API_URL}',
            True,  # Zawsze OK — tylko informacja
        )
        check(
            'KSEF_NIP jest ustawiony',
            bool(ksef_nip) and ksef_nip.isdigit() and len(ksef_nip) == 10,
            'Ustaw KSEF_NIP (10 cyfr, bez kresek) w .env',
        )
        check(
            'KSEF_TOKEN jest ustawiony',
            bool(ksef_token) and not _is_placeholder(ksef_token),
            'Wygeneruj token w panelu KSeF (zakładka "Zarządzanie tokenami")',
        )

        self.stdout.write('\n=== KSEF SERVICE (WAŻNE!) ===')
        self.stdout.write(self.style.WARNING(
            '  [!!]  ksef_service.py to MOCK — faktury NIE są wysyłane do prawdziwego KSeF!\n'
            '         Token z .env jest skonfigurowany, ale NIE jest używany przez ksef_service.py.\n'
            '         Aby faktury trafiały do KSeF MF, zastąp funkcję submit() w invoices/ksef_service.py\n'
            '         prawdziwą integracją (sesja interaktywna / token serwisowy + XML FA(2)).'
        ))

        self.stdout.write('\n=== BAZA DANYCH ===')
        check(
            f'DB_ENGINE={settings.DATABASES["default"]["ENGINE"]}',
            True,
        )
        check(
            'Nie używa SQLite na produkcji',
            'sqlite3' not in settings.DATABASES['default']['ENGINE'],
            'Na produkcji użyj MySQL lub PostgreSQL (DB_ENGINE w .env)',
        )

        self.stdout.write('\n=== LOGI ===')
        log_dir = getattr(settings, 'LOG_DIR', None)
        check(
            f'Katalog logów: {log_dir}',
            log_dir is not None and log_dir.exists(),
            'Upewnij się że katalog logs/ jest zapisywalny',
        )

        self.stdout.write('')
        if ok:
            self.stdout.write(self.style.SUCCESS('Wszystkie krytyczne zmienne są poprawnie ustawione.\n'))
        else:
            self.stdout.write(self.style.ERROR(
                'Znaleziono problemy z konfiguracją. Uzupełnij .env przed uruchomieniem produkcyjnym.\n'
            ))
