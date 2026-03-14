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

    # Ustawienia widoczności na PDF
    show_logo_on_pdf = models.BooleanField(default=True, verbose_name="Pokazuj logo na PDF")
    show_signature_on_pdf = models.BooleanField(default=True, verbose_name="Pokazuj podpis na PDF")

    def __str__(self):
        # Ładne wyświetlanie w panelu admina
        if self.is_company:
            return f"[Firma] {self.company_name or self.email}"
        # first_name i last_name są dziedziczone z AbstractUser
        full_name = f"{self.first_name} {self.last_name}".strip()
        if full_name:
            return f"[Osoba] {full_name} ({self.email})"
        return f"[Użytkownik] {self.email}"

class UserLogo(models.Model):
    """Model przechowujący wiele logotypów użytkownika."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='logos', verbose_name="Użytkownik")
    image = models.ImageField(upload_to='user_logos/', verbose_name="Plik loga")

    # Ustawienia specyficzne dla tego loga
    width = models.IntegerField(default=45, verbose_name="Szerokość (mm)")
    height = models.IntegerField(default=20, verbose_name="Wysokość (mm)")

    LOGO_POSITIONS = (
        ('right', 'Po prawej stronie tytułu'),
        ('left', 'Po lewej stronie tytułu'),
        ('top_center', 'Wyśrodkowane na górze (nad tytułem)'),
    )
    position = models.CharField(max_length=20, choices=LOGO_POSITIONS, default='right', verbose_name="Pozycja")
    theme_color = models.CharField(max_length=7, default='#1565C0', verbose_name="Kolor motywu (HEX)")

    name = models.CharField(max_length=100, blank=True, verbose_name="Nazwa własna loga (np. marka)")
    is_default = models.BooleanField(default=False, verbose_name="Domyślne")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Logo użytkownika"
        verbose_name_plural = "Logotypy użytkownika"

    def __str__(self):
        return f"Logo {self.name or self.id} - {self.user.email}"

    def save(self, *args, **kwargs):
        # Jeśli to logo ma być domyślne, odznacz inne loga tego użytkownika
        if self.is_default:
            UserLogo.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class UserSignature(models.Model):
    """Model przechowujący podpisy użytkownika (np. skan podpisu/pieczątki)."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='signatures', verbose_name="Użytkownik")
    image = models.ImageField(upload_to='user_signatures/', verbose_name="Plik podpisu")

    # Ustawienia specyficzne dla tego podpisu
    width = models.IntegerField(default=60, verbose_name="Szerokość (mm)")
    height = models.IntegerField(default=30, verbose_name="Wysokość (mm)")

    SIGNATURE_POSITIONS = (
        ('bottom_right', 'Po prawej na dole'),
        ('bottom_left', 'Po lewej na dole'),
        ('bottom_center', 'Wyśrodkowane na dole'),
    )
    position = models.CharField(max_length=20, choices=SIGNATURE_POSITIONS, default='bottom_right', verbose_name="Pozycja")

    name = models.CharField(max_length=100, blank=True, verbose_name="Nazwa podpisu (np. Jan Kowalski)")
    is_default = models.BooleanField(default=False, verbose_name="Domyślne")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Podpis użytkownika"
        verbose_name_plural = "Podpisy użytkownika"

    def __str__(self):
        return f"Podpis {self.name or self.id} - {self.user.email}"

    def save(self, *args, **kwargs):
        # Jeśli ten podpis ma być domyślny, odznacz inne podpisy tego użytkownika
        if self.is_default:
            UserSignature.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
