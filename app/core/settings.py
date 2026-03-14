"""
Django settings for core project.
Skonfigurowane dla: Django + DRF + SimpleJWT + dj-rest-auth + Allauth + Axes.
Poziom bezpieczeństwa: WYSOKI (HttpOnly Cookies, CSRF, Password Policy, Brute-force protection).
"""

from pathlib import Path
from datetime import timedelta

# Budowanie ścieżek wewnątrz projektu
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 1. KONFIGURACJA PODSTAWOWA I BEZPIECZEŃSTWO
# ==============================================================================

# [ZMIEŃ TO NA PRODUKCJI]
# Klucz kryptograficzny. Musi być tajny. Jeśli wycieknie, hakerzy mogą podpisywać fałszywe sesje.
# Na produkcji użyj np. os.environ.get('SECRET_KEY')
SECRET_KEY = 'django-insecure-gcgc_@q^ulas&@sl)gk86v8(wc#e0q6*wvbkb06o(t)ftx$(r2'

# [ZMIEŃ TO NA PRODUKCJI]
# True = widzisz błędy w przeglądarce (Developerka).
# False = użytkownik widzi tylko "Server Error 500" (Produkcja).
DEBUG = True

# [ZMIEŃ TO NA PRODUKCJI]
# Lista domen, pod którymi działa backend. Na produkcji np. ['api.mojanazwa.pl']
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "51.75.65.27"
]


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
        'DIRS': [],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================================================================
# MODEL UŻYTKOWNIKA I HASŁA
# ==============================================================================

# Wskazujemy Django, żeby używał naszego modelu zamiast domyślnego User
AUTH_USER_MODEL = 'users.CustomUser'

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
if DEBUG:
    # Na developerce e-maile są wyświetlane w konsoli, a nie wysyłane
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # Na produkcji podaj prawdziwe dane swojego serwera SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.example.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'your-email@example.com'
    EMAIL_HOST_PASSWORD = 'your-email-password'

# Adresy e-mail serwisu
SITEEMAIL = 'info@wyznaczresurs.com' # Główny e-mail do odbierania wiadomości
DEFAULT_FROM_EMAIL = 'noreply@wyznaczresurs.com' # Adres "od" dla automatycznych wiadomości

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
ACCOUNT_EMAIL_VERIFICATION = 'none' # Zmień na 'mandatory' na produkcji
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True

# ==============================================================================
# CORS & CSRF (Połączenie z Frontendem)
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "http://51.75.65.27",
    "http://51.75.65.27:9000"
]
CORS_ALLOW_CREDENTIALS = True 
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    "http://51.75.65.27",
    "http://51.75.65.27:9000"
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
import os
PAYPAL_SANDBOX = DEBUG  # True = sandbox.paypal.com, False = api.paypal.com
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', 'SANDBOX_CLIENT_ID_TUTAJ')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', 'SANDBOX_SECRET_TUTAJ')
