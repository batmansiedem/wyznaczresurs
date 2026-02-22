from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Oczekująca')),
        ('sent', _('Wysłana do KSeF')),
        ('accepted', _('Zaakceptowana przez KSeF')),
        ('rejected', _('Odrzucona przez KSeF')),
        ('cancelled', _('Anulowana')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_("Użytkownik")
    )
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name=_("Numer faktury"))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Kwota netto"))
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Kwota VAT"))
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Kwota brutto"))
    
    points_added = models.IntegerField(default=0, verbose_name=_("Dodane punkty"))
    
    # KSeF related fields
    ksef_reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Numer referencyjny KSeF"))
    ksef_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Status KSeF"))
    
    issue_date = models.DateField(auto_now_add=True, verbose_name=_("Data wystawienia"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Metadane firmy w momencie wystawienia (historyczne)
    buyer_name = models.CharField(max_length=255, verbose_name=_("Nazwa nabywcy"))
    buyer_nip = models.CharField(max_length=20, verbose_name=_("NIP nabywcy"))
    buyer_address = models.TextField(verbose_name=_("Adres nabywcy"))

    class Meta:
        verbose_name = _("Faktura")
        verbose_name_plural = _("Faktury")
        ordering = ['-issue_date', '-id']

    def __str__(self):
        return f"{self.invoice_number} - {self.user.email}"
