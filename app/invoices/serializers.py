from rest_framework import serializers
from .models import Invoice
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'company_name', 'nip', 'premium')

class InvoiceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    ksef_qr_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('invoice_number', 'ksef_reference_number', 'ksef_status', 'issue_date', 'created_at')

    def get_ksef_qr_url(self, obj):
        if not obj.ksef_invoice_hash or not obj.ksef_reference_number:
            return None
        from django.conf import settings

        is_sandbox = getattr(settings, 'KSEF_SANDBOX', True)
        host = 'qr-test.ksef.mf.gov.pl' if is_sandbox else 'qr.ksef.mf.gov.pl'
        inv_hash = obj.ksef_invoice_hash.replace('+', '-').replace('/', '_').rstrip('=')
        return f"https://{host}/{obj.ksef_reference_number}/{inv_hash}"

class CreateInvoiceSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    # Można podać net_amount (netto) LUB gross_amount (brutto) — jedno z nich jest wymagane
    net_amount   = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    gross_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    points_to_add = serializers.IntegerField()
    is_proforma = serializers.BooleanField(default=False)
    service_name = serializers.CharField(max_length=255, required=False)

    buyer_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    buyer_nip = serializers.CharField(max_length=20, required=False, allow_blank=True)
    buyer_address = serializers.CharField(style={'base_template': 'textarea.html'}, required=False, allow_blank=True)

    recipient_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    recipient_address = serializers.CharField(style={'base_template': 'textarea.html'}, required=False, allow_blank=True)

    payment_terms = serializers.ChoiceField(choices=Invoice.PAYMENT_TERM_CHOICES, default="paid")

    def validate(self, attrs):
        if not attrs.get('net_amount') and not attrs.get('gross_amount'):
            raise serializers.ValidationError(
                "Podaj kwotę netto (net_amount) lub brutto (gross_amount)."
            )
        return attrs

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Użytkownik o podanym ID nie istnieje.")
        return value


class CreateCorrectionSerializer(serializers.Serializer):
    net_amount   = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    gross_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(max_length=500)

    def validate(self, attrs):
        if not attrs.get('net_amount') and not attrs.get('gross_amount'):
            raise serializers.ValidationError(
                "Podaj skorygowaną kwotę netto (net_amount) lub brutto (gross_amount)."
            )
        return attrs
