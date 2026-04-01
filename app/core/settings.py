"""
Django settings for core project.
Skonfigurowane dla: Django + DRF + SimpleJWT + dj-rest-auth + Allauth + Axes.
Poziom bezpieczeństwa: WYSOKI (HttpOnly Cookies, CSRF, Password Policy, Brute-force protection).
"""

from pathlib import Path
from datetime import timedelta
import os
import logging.handlers
from dotenv import load_dotenv

# Budowanie ścieżek wewnątrz projektu
BASE_DIR = Path(__file__).resolve().parent.parent

# Wczytaj zmienne z pliku app/.env (jeśli istnieje — na produkcji musi istnieć)
load_dotenv(BASE_DIR / '.env')

# ==============================================================================
# 1. KONFIGURACJA PODSTAWOWA I BEZPIECZEŃSTWO
# ==============================================================================

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-gcgc_@q^ulas&@sl)gk86v8(wc#e0q6*wvbkb06o(t)ftx$(r2')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')]


# ==============================================================================
# APLIKACJE (INSTALLED_APPS)
# ==============================================================================

INSTALLED_APPS = [
    # --- Aplikacje wbudowane Django ---
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # --- Biblioteki zewnętrzne ---
    'rest_framework',           # Główne API
    'rest_framework.authtoken', # Wymagane przez dj-rest-auth
    'corsheaders',              # Obsługa zapytań z innej domeny (Frontend)
    'dj_rest_auth',             # Gotowe endpointy logowania/wylogowania
    'django.contrib.sites',     # Wymagane przez allauth
    'allauth',                  # Logika autoryzacji (rejestracja, reset hasła)
    'allauth.account',          # Zarządzanie kontami
    'allauth.socialaccount',    # Logowanie społecznościowe (FB/Google) - wymagane przez allauth
    'dj_rest_auth.registration',# Endpoint rejestracji
    'axes',                     # Ochrona przed Brute-Force (blokowanie IP)
    'django_password_validators', # Zaawansowana polityka haseł
    "django_password_validators.password_history",
    'django_filters',           # Filtrowanie i wyszukiwanie w API

    # --- Twoje aplikacje ---
    'users',                    # Twój niestandardowy model użytkownika
    'calculators',              # Nowa aplikacja do kalkulatorów
    'specialists',              # Nowa aplikacja dla specjalistów (konserwatorów)
    'contacts',                 # Nowa aplikacja dla formularza kontaktowego
    'invoices',                 # Nowa aplikacja do faktur i punktów
    'notifications',            # Nowa aplikacja do powiadomień
]

# Wymagane przez django.contrib.sites i allauth
SITE_ID = 1

# ==============================================================================
# MIDDLEWARE (Kolejność jest krytyczna!)
# ==============================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',            # 1. Musi być na samej górze (obsługa CORS)
    'django.middleware.security.SecurityMiddleware',    # 2. Bezpieczeństwo HTTP
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'axes.middleware.AxesMiddleware',                   # 3. Axes musi śledzić zapytania przed autoryzacją
    'django.middleware.csrf.CsrfViewMiddleware',        # 4. Ochrona formularzy przed CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware'          # 5. Wymagane przez allauth
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Wymagane przez allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ==============================================================================
# BAZA DANYCH
# ==============================================================================

_db_engine = os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3')
_db_name   = os.environ.get('DB_NAME', 'db.sqlite3')
DATABASES = {
    'default': {
        'ENGINE': _db_engine,
        'NAME': BASE_DIR / _db_name if _db_engine.endswith('sqlite3') else _db_name,
        'USER':     os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     os.environ.get('DB_PORT', ''),
    }
}

# ==============================================================================
# MODEL UŻYTKOWNIKA I HASŁA
# ==============================================================================

# Wskazujemy Django, żeby używał naszego modelu zamiast domyślnego User
AUTH_USER_MODEL = 'users.CustomUser'

# Obsługa hashy bcrypt (migracja ze starej aplikacji PHP)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

# Polityka haseł - Tutaj ustalasz jak trudne musi być hasło
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': { 'min_length': 8 } },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator' },
    { 'NAME': 'django_password_validators.password_character_requirements.password_validation.PasswordCharacterValidator', 'OPTIONS': { 'min_length_digit': 1, 'min_length_alpha': 1, 'min_length_special': 1, 'min_length_lower': 1, 'min_length_upper': 1, 'special_characters': "~!@#$%^&*()_+{}\":;'[]" } },
    { 'NAME': 'django_password_validators.password_history.password_validation.UniquePasswordsValidator', "OPTIONS": {"last_passwords": 5} }
]

# ==============================================================================
# LOKALIZACJA I E-MAIL
# ==============================================================================

LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static_root'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Konfiguracja E-mail
EMAIL_HOST          = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL       = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT       = 10  # sekundy — timeout połączenia SMTP

# Obejście dla Python 3.14+ (problemy z weryfikacją certyfikatu Basic Constraints)
if os.environ.get('EMAIL_SSL_NO_VERIFY', 'True') == 'True':
    import ssl
    context = ssl._create_unverified_context()
    EMAIL_SSL_CONTEXT = context

if EMAIL_HOST:
    if os.environ.get('EMAIL_SSL_NO_VERIFY', 'True') == 'True':
        EMAIL_BACKEND = 'core.email_backend.UnverifiedSSLEmailBackend'
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'info@wyznaczresurs.com')
SITEEMAIL          = os.environ.get('SITE_EMAIL', 'kontakt@wyznaczresurs.com')
SITE_NAME          = 'wyznaczresurs.com'


# ==============================================================================
# KONFIGURACJA API (DRF & JWT)
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ==============================================================================
# KONFIGURACJA DJ-REST-AUTH (Ciasteczka HttpOnly)
# ==============================================================================

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access_token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh_token',
    'JWT_AUTH_HTTPONLY': True,
    'JWT_AUTH_SAMESITE': 'Lax',
    'JWT_AUTH_SECURE': not DEBUG, 
    'SESSION_LOGIN': False,
    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',
    'USER_DETAILS_SERIALIZER': 'users.serializers.CustomUserDetailsSerializer',
}

# ==============================================================================
# KONFIGURACJA ALLAUTH (Logika konta)
# ==============================================================================
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_ADAPTER = 'users.adapter.CustomAccountAdapter'

# ==============================================================================
# CORS & CSRF (Połączenie z Frontendem)
# ==============================================================================
_frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:9000')
CORS_ALLOWED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    _frontend_url,
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    _frontend_url,
]
CSRF_COOKIE_HTTPONLY = False 
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG

# ==============================================================================
# OCHRONA BRUTE-FORCE (AXES)
# ==============================================================================
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend', 
    'django.contrib.auth.backends.ModelBackend', 
    'allauth.account.auth_backends.AuthenticationBackend',
]
AXES_FAILURE_LIMIT = 5            
AXES_COOLOFF_TIME = 1             
AXES_RESET_ON_SUCCESS = True      
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]
AXES_ONLY_USER_LOCKOUT = False

# ==============================================================================
# PAYPAL (Sandbox — zmień na produkcji)
# Utwórz aplikację sandbox na: https://developer.paypal.com/developer/applications
# ==============================================================================
PAYPAL_SANDBOX        = os.environ.get('PAYPAL_SANDBOX', 'True') == 'True'
PAYPAL_CLIENT_ID      = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET  = os.environ.get('PAYPAL_CLIENT_SECRET', '')

# Backup bazy danych
BACKUP_DIR       = os.environ.get('BACKUP_DIR', str(BASE_DIR / 'backups'))
BACKUP_KEEP_LAST = int(os.environ.get('BACKUP_KEEP_LAST', '30'))

# KSeF — Krajowy System e-Faktur
KSEF_SANDBOX = os.environ.get('KSEF_SANDBOX', 'True') != 'False'
KSEF_NIP     = os.environ.get('KSEF_NIP', '')
KSEF_TOKEN   = os.environ.get('KSEF_TOKEN', '')
KSEF_API_URL = 'https://api-test.ksef.mf.gov.pl/v2' if KSEF_SANDBOX else 'https://api.ksef.mf.gov.pl/v2'

# ==============================================================================
# LOGOWANIE (LOGGING)
# ==============================================================================

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_app': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'app.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_transactions': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'transactions.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        # Błędy Django (500, złe zapytania itp.)
        'django.request': {
            'handlers': ['console', 'file_app'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.core.mail': {
            'handlers': ['console', 'file_app'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'allauth': {
            'handlers': ['console', 'file_app'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Faktury, KSeF, PayPal
        'invoices': {
            'handlers': ['console', 'file_app', 'file_transactions'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        # Kalkulatory (obliczenia, punkty)
        'calculators': {
            'handlers': ['console', 'file_app'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_app'],
        'level': 'WARNING',
    },
}

# ==============================================================================
# KONFIGURACJA FAKTUR
# ==============================================================================
INVOICE_SELLER_DATA = {
    'name': 'EDS Dariusz Surmacki',
    'address': 'ul. Lawinowa 36C, 92-010 Łódź',
    'nip': '7691427583',
    'bank_account': '60 1240 3116 1111 0010 9288 1740',
    'email': 'info@wyznaczresurs.com',
}
