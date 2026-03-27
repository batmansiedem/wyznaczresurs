from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import UserLogo, UserSignature

User = get_user_model()

class UserLogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLogo
        fields = (
            'id', 'image', 'width', 'height', 'position',
            'theme_color', 'name', 'is_default', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

class UserSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSignature
        fields = (
            'id', 'image', 'width', 'height', 'position',
            'name', 'is_default', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

class CustomUserDetailsSerializer(UserDetailsSerializer):
    """Serializer profilu użytkownika dla GET/PUT/PATCH /auth/user/."""
    logos = UserLogoSerializer(many=True, read_only=True)
    signatures = UserSignatureSerializer(many=True, read_only=True)

    class Meta(UserDetailsSerializer.Meta):
        model = User
        fields = (
            'pk', 'email', 'first_name', 'last_name',
            'is_company', 'company_name', 'nip',
            'address_line', 'postal_code', 'city', 'premium',
            'discount_percent',
            'is_staff', 'is_superuser',
            'has_custom_logo', 'custom_logo',
            'logo_width', 'logo_height', 'logo_position',
            'theme_color', 'show_logo_on_pdf', 'show_signature_on_pdf', 'logos', 'signatures',
        )
        read_only_fields = ('pk', 'email', 'premium', 'discount_percent', 'is_staff', 'is_superuser', 'has_custom_logo')

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


# --- SERIALIZERY PANELU ADMINISTRATORA ---

class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer listy użytkowników dla admina — ze statystykami."""
    transaction_count = serializers.IntegerField(read_only=True)
    invoice_count = serializers.IntegerField(read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'display_name',
            'is_company', 'company_name', 'nip',
            'address_line', 'postal_code', 'city',
            'premium', 'discount_percent', 'is_staff', 'is_superuser', 'is_active',
            'date_joined', 'last_login',
            'transaction_count', 'invoice_count',
            'has_custom_logo', 'show_logo_on_pdf', 'show_signature_on_pdf',
        )

    def get_display_name(self, obj):
        if obj.is_company:
            return obj.company_name or obj.email
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or obj.email


class AdminUserDetailSerializer(AdminUserListSerializer):
    """Pełny serializer użytkownika dla widoku szczegółowego admina."""
    class Meta(AdminUserListSerializer.Meta):
        fields = AdminUserListSerializer.Meta.fields


class AdminCreateUserSerializer(serializers.Serializer):
    """Serializer tworzenia użytkownika przez admina (np. po NIP)."""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    is_company = serializers.BooleanField(default=False)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    nip = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    address_line = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    postal_code = serializers.CharField(max_length=10, required=False, allow_blank=True, default='')
    city = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    password = serializers.CharField(min_length=8, write_only=True, required=False, default='')
    premium = serializers.IntegerField(default=0, min_value=0)
    discount_percent = serializers.IntegerField(default=0, min_value=0, max_value=100)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Użytkownik z tym adresem email już istnieje.")
        return value

    def validate(self, data):
        if data.get('is_company'):
            if not data.get('nip'):
                raise serializers.ValidationError({"nip": "NIP jest wymagany dla kont firmowych."})
        return data


class AdminUpdateUserSerializer(serializers.ModelSerializer):
    """Serializer edycji użytkownika przez admina."""
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'is_company', 'company_name', 'nip',
            'address_line', 'postal_code', 'city', 'premium', 'discount_percent', 'is_active',
            'show_logo_on_pdf', 'show_signature_on_pdf',
        )
