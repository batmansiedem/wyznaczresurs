from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

# 1. MANAGER UŻYTKOWNIKA (Niezbędny do logowania e-mailem)
class CustomUserManager(BaseUserManager):
    """
    Niestandardowy menedżer, który każe Django używać emaila jako
    unikalnego identyfikatora zamiast username.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Adres email jest wymagany'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser musi mieć is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser musi mieć is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

# 2. MODEL UŻYTKOWNIKA
class CustomUser(AbstractUser):
    # --- KONFIGURACJA LOGOWANIA EMAILEM ---
    username = None  # Usuwamy pole username z bazy danych
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS musi być puste! Email i hasło są wymagane przez system domyślnie.
    REQUIRED_FIELDS = [] 

    # Podpinamy nasz manager zdefiniowany wyżej
    objects = CustomUserManager()
    # ---------------------------------------

    # --- TWOJE POLA ---
    # Flaga: True = Firma, False = Osoba prywatna
    is_company = models.BooleanField(default=False, verbose_name="Czy to firma?")

    # Dane do faktury (NIP i Nazwa firmy opcjonalne w bazie)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    
    # NIP trzymamy opcjonalny na poziomie bazy. Frontend wymusi go, jeśli is_company=True.
    nip = models.CharField(max_length=20, blank=True, null=True)

    # Adres (Wspólny dla obu typów)
    address_line = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    premium = models.IntegerField(default=0, verbose_name="Punkty Premium")

    # Własne logo na obliczeniach (wykupowane za 200 pkt)
    has_custom_logo = models.BooleanField(default=False, verbose_name="Ma wykupione własne logo")
    custom_logo = models.ImageField(upload_to='user_logos/', blank=True, null=True, verbose_name="Plik loga")
    
    # Ustawienia wyświetlania loga
    LOGO_POSITIONS = (
        ('right', 'Po prawej stronie tytułu'),
        ('left', 'Po lewej stronie tytułu'),
        ('top_center', 'Wyśrodkowane na górze (nad tytułem)'),
    )
    logo_width = models.IntegerField(default=45, verbose_name="Szerokość loga (mm)")
    logo_height = models.IntegerField(default=20, verbose_name="Wysokość loga (mm)")
    logo_position = models.CharField(max_length=20, choices=LOGO_POSITIONS, default='right', verbose_name="Pozycja loga")
    theme_color = models.CharField(max_length=7, default='#1565C0', verbose_name="Kolor motywu (HEX)")

    def __str__(self):
        # Ładne wyświetlanie w panelu admina
        if self.is_company:
            return f"[Firma] {self.company_name or self.email}"
        # first_name i last_name są dziedziczone z AbstractUser
        full_name = f"{self.first_name} {self.last_name}".strip()
        if full_name:
            return f"[Osoba] {full_name} ({self.email})"
        return f"[Użytkownik] {self.email}"