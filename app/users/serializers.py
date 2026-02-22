from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """Serializer profilu użytkownika dla GET/PUT/PATCH /auth/user/."""

    class Meta(UserDetailsSerializer.Meta):
        model = User
        fields = (
            'pk', 'email', 'first_name', 'last_name',
            'is_company', 'company_name', 'nip',
            'address_line', 'postal_code', 'city', 'premium',
            'is_staff', 'is_superuser',
        )
        read_only_fields = ('pk', 'email', 'premium', 'is_staff', 'is_superuser')

class CustomRegisterSerializer(RegisterSerializer):
    # 1. ZABEZPIECZENIE: Wyłączamy username w serializerze
    username = None

    # Pola niestandardowe
    is_company = serializers.BooleanField(default=False)
    company_name = serializers.CharField(required=False, allow_blank=True)
    nip = serializers.CharField(required=False, allow_blank=True)
    
    # Dane adresowe i osobowe
    address_line = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    # 2. WALIDACJA LOGICZNA (Backend musi pilnować spójności danych)
    def validate(self, data):
        # Wykonujemy standardową walidację (np. unikalność emaila)
        data = super().validate(data)
        
        # Sprawdzamy logikę firmy
        if data.get('is_company', False):
            if not data.get('company_name'):
                raise serializers.ValidationError({"company_name": "Nazwa firmy jest wymagana dla kont firmowych."})
            if not data.get('nip'):
                raise serializers.ValidationError({"nip": "NIP jest wymagany dla kont firmowych."})
        
        return data

    @transaction.atomic
    def custom_signup(self, request, user):
        # Przepisanie danych z requestu do modelu usera
        data = self.validated_data
        
        user.is_company = data.get('is_company', False)
        user.company_name = data.get('company_name', '')
        user.nip = data.get('nip', '')
        
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        
        user.address_line = data.get('address_line', '')
        user.postal_code = data.get('postal_code', '')
        user.city = data.get('city', '')
        
        user.save()