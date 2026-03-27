from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class CalculatorDefinition(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Nazwa kalkulatora"))
    slug = models.SlugField(unique=True, max_length=255, verbose_name=_("Slug URL"))
    description = models.TextField(blank=True, verbose_name=_("Opis"))

    is_active = models.BooleanField(default=True, verbose_name=_("Aktywny"))
    
    # Premium cost for using this calculator (if applicable)
    premium_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=100.00,
        verbose_name=_("Koszt premium (nowy resurs)")
    )
    premium_cost_recurring = models.DecimalField(
        max_digits=10, decimal_places=2, default=80.00,
        verbose_name=_("Koszt premium (ponowny resurs)")
    )

    class Meta:
        verbose_name = _("Definicja kalkulatora")
        verbose_name_plural = _("Definicje kalkulatorów")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class CalculatorResult(models.Model):
    calculator_definition = models.ForeignKey(
        CalculatorDefinition,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_("Definicja kalkulatora")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calculator_results',
        verbose_name=_("Użytkownik")
    )
    input_data = models.JSONField(verbose_name=_("Dane wejściowe"))
    output_data = models.JSONField(verbose_name=_("Dane wyjściowe"))
    is_locked = models.BooleanField(default=False, verbose_name=_("Wyniki zablokowane"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Data utworzenia"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Data ostatniej aktualizacji"))

    class Meta:
        verbose_name = _("Wynik kalkulatora")
        verbose_name_plural = _("Wyniki kalkulatorów")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.calculator_definition.name} - {self.user.email} ({self.created_at.strftime('%Y-%m-%d')})"

class Unit(models.Model):
    UNIT_TYPES = (
        ('length', _('Długość')),
        ('mass', _('Masa')),
        ('time', _('Czas')),
        ('area', _('Powierzchnia')),
        ('volume', _('Objętość')),
        ('force', _('Siła')),
        ('pressure', _('Ciśnienie')),
        ('energy', _('Energia')),
        ('power', _('Moc')),
        ('temperature', _('Temperatura')),
        ('currency', _('Waluta')),
        ('velocity', _('Prędkość')),
        ('dimensionless', _('Bezjednostkowe')),
    )

    name = models.CharField(max_length=50, verbose_name=_("Nazwa jednostki"))
    symbol = models.CharField(max_length=10, unique=True, verbose_name=_("Symbol jednostki"))
    unit_type = models.CharField(max_length=50, choices=UNIT_TYPES, verbose_name=_("Typ jednostki"))
    # Conversion factor to a common base unit for its unit_type.
    # E.g., for 'length', if 'meter' is base (factor=1.0), then 'foot' might be 0.3048.
    conversion_factor = models.DecimalField(
        max_digits=20, decimal_places=10,
        help_text=_("Współczynnik konwersji do podstawowej jednostki typu (np. dla długości: metra).")
    )

    class Meta:
        verbose_name = _("Jednostka")
        verbose_name_plural = _("Jednostki")
        unique_together = ('unit_type', 'name') # Ensures unique unit names per type

    def __str__(self):
        return f"{self.name} ({self.symbol}) - {self.get_unit_type_display()}"
