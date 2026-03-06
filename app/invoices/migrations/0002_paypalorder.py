from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("invoices", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Dodaj blank=True do buyer_nip i buyer_address (były wymagane)
        migrations.AlterField(
            model_name="invoice",
            name="buyer_nip",
            field=models.CharField(blank=True, max_length=20, verbose_name="NIP nabywcy"),
        ),
        migrations.AlterField(
            model_name="invoice",
            name="buyer_address",
            field=models.TextField(blank=True, verbose_name="Adres nabywcy"),
        ),
        # Nowy model PayPalOrder
        migrations.CreateModel(
            name="PayPalOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("paypal_order_id", models.CharField(max_length=100, unique=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("points", models.IntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Utworzone"),
                            ("completed", "Opłacone"),
                            ("failed", "Błąd"),
                        ],
                        default="created",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "invoice",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="paypal_order",
                        to="invoices.invoice",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="paypal_orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
