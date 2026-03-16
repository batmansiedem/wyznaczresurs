from .models import Unit
from django.core.exceptions import ValidationError
from decimal import Decimal


def decimals_to_float(obj):
    """Rekurencyjnie konwertuje wartości Decimal na float dla serializacji JSON."""
    if isinstance(obj, dict):
        return {k: decimals_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decimals_to_float(v) for v in obj]
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

def convert_unit(value, from_unit_symbol, to_unit_symbol):
    """
    Converts a value from one unit to another.

    Args:
        value (Decimal or float): The value to convert.
        from_unit_symbol (str): The symbol of the unit to convert from (e.g., 'm', 'ft').
        to_unit_symbol (str): The symbol of the unit to convert to (e.g., 'cm', 'in').

    Returns:
        Decimal: The converted value.

    Raises:
        ValidationError: If units are not found, are of different types, or conversion factor is invalid.
    """
    if from_unit_symbol == to_unit_symbol:
        return Decimal(value)

    try:
        from_unit = Unit.objects.get(symbol=from_unit_symbol)
        to_unit = Unit.objects.get(symbol=to_unit_symbol)
    except Unit.DoesNotExist:
        raise ValidationError(f"Jednostka '{from_unit_symbol}' lub '{to_unit_symbol}' nie została znaleziona.")

    if from_unit.unit_type != to_unit.unit_type:
        raise ValidationError(
            f"Nie można konwertować jednostek różnych typów: {from_unit.unit_type} do {to_unit.unit_type}."
        )

    try:
        # Convert value to the base unit
        value_in_base_unit = Decimal(value) * from_unit.conversion_factor
        # Convert from base unit to the target unit
        converted_value = value_in_base_unit / to_unit.conversion_factor
    except (TypeError, ValueError, ZeroDivisionError) as e:
        raise ValidationError(f"Błąd podczas konwersji jednostek: {e}")

    return converted_value
