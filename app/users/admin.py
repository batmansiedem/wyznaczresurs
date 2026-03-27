from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserLogo

class UserLogoInline(admin.TabularInline):
    model = UserLogo
    extra = 1
    fields = ('name', 'image', 'width', 'height', 'position', 'theme_color', 'is_default')

@admin.register(UserLogo)
class UserLogoAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_default', 'created_at')
    list_filter = ('is_default', 'position')
    search_fields = ('name', 'user__email', 'user__company_name')

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    inlines = [UserLogoInline]
    
    # 1. NAPRAWA BŁĘDU: Sortowanie po emailu zamiast username
    ordering = ('email',)
    
    # 2. LISTA: Co widać w tabeli użytkowników
    list_display = ('email', 'first_name', 'last_name', 'is_company', 'company_name', 'is_staff', 'premium', 'discount_percent')
    
    # 3. FILTRY: Po czym można filtrować z boku
    list_filter = ('is_company', 'is_staff', 'is_superuser', 'is_active')
    
    # 4. WYSZUKIWANIE: Po czym można szukać (email, nip, nazwa firmy)
    search_fields = ('email', 'first_name', 'last_name', 'company_name', 'nip')

    # 5. EDYCJA: Układ pól w formularzu edycji użytkownika
    # Musimy usunąć 'username' i dodać Twoje pola (nip, adres itp.)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dane osobowe', {'fields': ('first_name', 'last_name')}),
        ('Status i Zniżki', {'fields': ('premium', 'discount_percent', 'has_custom_logo')}),
        ('Dane Firmowe', {'fields': ('is_company', 'company_name', 'nip')}),
        ('Adres', {'fields': ('address_line', 'postal_code', 'city')}),
        ('Uprawnienia', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Ważne daty', {'fields': ('last_login', 'date_joined')}),
        ('Stare pola loga (fallback)', {'fields': ('custom_logo', 'logo_width', 'logo_height', 'logo_position', 'theme_color'), 'classes': ('collapse',)}),
    )

    # 6. DODAWANIE: Układ pól przy tworzeniu nowego usera przez admina
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2', 'is_company', 'company_name', 'nip', 'first_name', 'last_name')}
        ),
    )

# Rejestrujemy model z naszą konfiguracją
admin.site.register(CustomUser, CustomUserAdmin)