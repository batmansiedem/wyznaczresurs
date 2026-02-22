from rest_framework import serializers
from .models import CalculatorDefinition, CalculatorResult, Unit

class CalculatorDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculatorDefinition
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'premium_cost']

class CalculatorDefinitionMinimalSerializer(serializers.ModelSerializer):
    """Minimalny serializer definicji — do osadzania w wynikach."""
    class Meta:
        model = CalculatorDefinition
        fields = ['id', 'name', 'slug']


class CalculatorResultSerializer(serializers.ModelSerializer):
    calculator_name = serializers.CharField(source='calculator_definition.name', read_only=True)
    calculator_slug = serializers.CharField(source='calculator_definition.slug', read_only=True)
    calculator_definition = CalculatorDefinitionMinimalSerializer(read_only=True)
    calculator_definition_id = serializers.PrimaryKeyRelatedField(
        queryset=CalculatorDefinition.objects.all(),
        source='calculator_definition', write_only=True, required=False,
    )

    class Meta:
        model = CalculatorResult
        fields = [
            'id', 'calculator_definition', 'calculator_definition_id',
            'calculator_name', 'calculator_slug', 'input_data', 'output_data',
            'is_locked', 'created_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_locked:
            data['output_data'] = {'is_locked': True}
        return data

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'symbol', 'unit_type', 'conversion_factor']
