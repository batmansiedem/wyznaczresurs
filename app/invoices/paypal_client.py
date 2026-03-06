"""
Klient PayPal Orders API v2 — bez zewnętrznego SDK (czyste requests).
Obsługuje sandbox i produkcję na podstawie PAYPAL_SANDBOX w settings.
"""
import uuid
import requests
from django.conf import settings


def _api_base() -> str:
    if settings.PAYPAL_SANDBOX:
        return "https://api-m.sandbox.paypal.com"
    return "https://api-m.paypal.com"


def _get_access_token() -> str:
    """Pobiera token OAuth2 metodą client_credentials."""
    response = requests.post(
        f"{_api_base()}/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def create_order(amount_pln: str, points: int, user_email: str) -> dict:
    """
    Tworzy zamówienie PayPal (intent=CAPTURE).
    Zwraca pełną odpowiedź JSON, w tym order['id'].
    """
    token = _get_access_token()
    response = requests.post(
        f"{_api_base()}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": str(uuid.uuid4()),
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "PLN",
                    "value": amount_pln,
                },
                "description": f"Doładowanie {points} pkt premium — wyznaczresurs.com",
                "custom_id": user_email,
            }],
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def capture_order(order_id: str) -> dict:
    """
    Przechwytuje (finalizuje) zatwierdzone zamówienie PayPal.
    Zwraca pełną odpowiedź JSON; status='COMPLETED' oznacza sukces.
    """
    token = _get_access_token()
    response = requests.post(
        f"{_api_base()}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": str(uuid.uuid4()),
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
