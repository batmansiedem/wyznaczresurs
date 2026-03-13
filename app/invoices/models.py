from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


# Pakiety doładowania — źródło prawdy dla backendu i frontendu
PAYPAL_PACKAGES = {
    "100":  {"points": 100,  "gross": Decimal("100.00")},
    "250":  {"points": 250,  "gross": Decimal("230.00")},
    "500":  {"points": 500,  "gross": Decimal("440.00")},
    "1000": {"points": 1000, "gross": Decimal("800.00")},
}


class Invoice(models.Model):
    STATUS_CHOICES = (
        ("pending",  _("Oczekująca")),
        ("sent",     _("Wysłana do KSeF")),
        ("accepted", _("Zaakceptowana przez KSeF")),
        ("rejected", _("Odrzucona przez KSeF")),
        ("cancelled", _("Anulowana")),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name=_("Użytkownik"),
    )
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name=_("Numer faktury"))
    net_amount   = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Kwota netto"))
    vat_amount   = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Kwota VAT"))
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Kwota brutto"))

    is_proforma = models.BooleanField(default=False, verbose_name=_("Proforma"))
    service_name = models.CharField(max_length=255, default="Wyznaczenie resursu UTB GTU_12", verbose_name=_("Nazwa usługi"))
    points_added = models.IntegerField(default=0, verbose_name=_("Dodane punkty"))

    # KSeF
    ksef_reference_number = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Numer referencyjny KSeF")
    )
    ksef_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name=_("Status KSeF")
    )

    issue_date = models.DateField(auto_now_add=True, verbose_name=_("Data wystawienia"))
    created_at = models.DateTimeField(auto_now_add=True)

    # Metadane nabywcy — snapshot w momencie wystawienia
    buyer_name    = models.CharField(max_length=255, verbose_name=_("Nazwa nabywcy"))
    buyer_nip     = models.CharField(max_length=20, blank=True, verbose_name=_("NIP nabywcy"))
    buyer_address = models.TextField(blank=True, verbose_name=_("Adres nabywcy"))

    # Odbiorca (opcjonalnie, np. dla samorządów)
    recipient_name    = models.CharField(max_length=255, blank=True, verbose_name=_("Nazwa odbiorcy"))
    recipient_address = models.TextField(blank=True, verbose_name=_("Adres odbiorcy"))

    # Warunki płatności
    PAYMENT_TERM_CHOICES = (
        ("paid", "Zapłacono przelewem"),
        ("7_days", "Do zapłaty w ciągu 7 dni"),
        ("14_days", "Do zapłaty w ciągu 14 dni"),
    )
    payment_terms = models.CharField(
        max_length=20, 
        choices=PAYMENT_TERM_CHOICES, 
        default="paid", 
        verbose_name=_("Warunki płatności")
    )

    class Meta:
        verbose_name = _("Faktura")
        verbose_name_plural = _("Faktury")
        ordering = ["-issue_date", "-id"]

    def __str__(self):
        return f"{self.invoice_number} - {self.user.email}"


class PayPalOrder(models.Model):
    """Śledzenie zamówień PayPal przed/po przechwyceniu płatności."""

    STATUS_CHOICES = (
        ("created",   "Utworzone"),
        ("completed", "Opłacone"),
        ("failed",    "Błąd"),
    )

    paypal_order_id = models.CharField(max_length=100, unique=True)
    amount  = models.DecimalField(max_digits=10, decimal_places=2)
    points  = models.IntegerField()
    status  = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    user    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paypal_orders",
    )
    invoice = models.OneToOneField(
        Invoice,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="paypal_order",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PayPal {self.paypal_order_id} — {self.user.email} — {self.status}"
