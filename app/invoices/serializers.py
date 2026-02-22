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
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('invoice_number', 'ksef_reference_number', 'ksef_status', 'issue_date', 'created_at')

class CreateInvoiceSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    points_to_add = serializers.IntegerField()
    
    # In a real app, these might come from the User model by default
    buyer_name = serializers.CharField(max_length=255, required=False)
    buyer_nip = serializers.CharField(max_length=20, required=False)
    buyer_address = serializers.CharField(style={'base_template': 'textarea.html'}, required=False)

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Użytkownik o podanym ID nie istnieje.")
        return value
