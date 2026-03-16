"""
Jednolity handler wyjątków DRF — wszystkie błędy API zwracają {"detail": "..."}.
Zastępuje domyślny handler DRF, który dla błędów walidacji zwraca {"field": ["error"]}.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Normalizuje odpowiedź błędów API do spójnego formatu {"detail": "..."}.
    Dzięki temu frontend zawsze odczytuje błąd z `error.response.data.detail`.
    """
    response = exception_handler(exc, context)

    if response is None:
        # Nieobsługiwany wyjątek (500) — zwróć generyczny komunikat
        return Response(
            {"detail": "Wystąpił błąd serwera. Spróbuj ponownie."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data

    # Jeśli data to już {"detail": "..."} — pozostaw bez zmian
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        return response

    # Spłaszcz błędy walidacji pól do jednego stringa dla frontendu
    if isinstance(data, dict):
        messages = []
        for key, value in data.items():
            if key == "non_field_errors":
                msgs = value if isinstance(value, list) else [value]
                messages.extend(str(m) for m in msgs)
            elif key != "detail":
                msgs = value if isinstance(value, list) else [value]
                messages.extend(f"{key}: {m}" for m in msgs)
            else:
                messages.append(str(value))
        response.data = {"detail": " | ".join(messages) if messages else "Błąd walidacji."}
    elif isinstance(data, list):
        response.data = {"detail": " | ".join(str(m) for m in data)}

    return response
