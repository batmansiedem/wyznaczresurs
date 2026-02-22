from django.db import models
from django.utils.translation import gettext_lazy as _

class Specialist(models.Model):
    VOIVODESHIP_CHOICES = [
        ('dolnośląskie', 'dolnośląskie'),
        ('kujawsko-pomorskie', 'kujawsko-pomorskie'),
        ('lubelskie', 'lubelskie'),
        ('lubuskie', 'lubuskie'),
        ('łódzkie', 'łódzkie'),
        ('małopolskie', 'małopolskie'),
        ('mazowieckie', 'mazowieckie'),
        ('opolskie', 'opolskie'),
        ('podkarpackie', 'podkarpackie'),
        ('podlaskie', 'podlaskie'),
        ('pomorskie', 'pomorskie'),
        ('śląskie', 'śląskie'),
        ('świętokrzyskie', 'świętokrzyskie'),
        ('warmińsko-mazurskie', 'warmińsko-mazurskie'),
        ('wielkopolskie', 'wielkopolskie'),
        ('zachodniopomorskie', 'zachodniopomorskie'),
    ]

    full_name = models.CharField(max_length=255, verbose_name=_("Imię i nazwisko"))
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Nazwa firmy"))
    scope_of_activities = models.TextField(blank=True, verbose_name=_("Zakres czynności"))
    contact_details = models.TextField(blank=True, verbose_name=_("Dane kontaktowe"))
    voivodeship = models.CharField(max_length=100, choices=VOIVODESHIP_CHOICES, blank=True, verbose_name=_("Województwo"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktywny"))

    class Meta:
        verbose_name = _("Specjalista")
        verbose_name_plural = _("Specjaliści")
        ordering = ['full_name', 'company_name']

    def __str__(self):
        if self.company_name:
            return f"{self.full_name} ({self.company_name})"
        return self.full_name
