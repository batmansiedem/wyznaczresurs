from django.contrib import admin
from .models import Invoice, PayPalOrder, BonusPointsCode

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'gross_amount', 'ksef_status', 'issue_date')
    list_filter = ('ksef_status', 'is_proforma', 'issue_date')
    search_fields = ('invoice_number', 'user__email', 'buyer_nip')

@admin.register(PayPalOrder)
class PayPalOrderAdmin(admin.ModelAdmin):
    list_display = ('paypal_order_id', 'user', 'amount', 'points', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('paypal_order_id', 'user__email')

@admin.register(BonusPointsCode)
class BonusPointsCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'points', 'is_active', 'used_by', 'used_at', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code', 'used_by__email')
    readonly_fields = ('created_at', 'used_at', 'used_by')
