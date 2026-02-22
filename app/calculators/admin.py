from django.contrib import admin
from .models import CalculatorDefinition, CalculatorResult, Unit

@admin.register(CalculatorDefinition)
class CalculatorDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'premium_cost')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(CalculatorResult)
class CalculatorResultAdmin(admin.ModelAdmin):
    list_display = ('calculator_definition', 'user', 'created_at')
    list_filter = ('calculator_definition', 'user', 'created_at')
    search_fields = ('user__email', 'calculator_definition__name')
    readonly_fields = ('created_at', 'updated_at', 'input_data', 'output_data')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'unit_type', 'conversion_factor')
    list_filter = ('unit_type',)
    search_fields = ('name', 'symbol')
