"""
Klient PayPal Orders API v2 — bez zewnętrznego SDK (czyste requests).
Obsługuje sandbox i produkcję na podstawie PAYPAL_SANDBOX w settings.
"""
import logging
import uuid
import requests
from django.conf import settings

logger = logging.getLogger('invoices.paypal')


def _api_base() -> str:
    if settings.PAYPAL_SANDBOX:
        return "https://api-m.sandbox.paypal.com"
    return "https://api-m.paypal.com"


def _get_access_token() -> str:
    """Pobiera token OAuth2 metodą client_credentials."""
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        logger.error(
            "PayPal: brak PAYPAL_CLIENT_ID lub PAYPAL_CLIENT_SECRET w konfiguracji. "
            "Uzupełnij zmienne środowiskowe."
        )
        raise ValueError("Brak konfiguracji PayPal (CLIENT_ID / CLIENT_SECRET).")

    sandbox_mode = settings.PAYPAL_SANDBOX
    logger.debug("PayPal: pobieranie access_token (sandbox=%s)", sandbox_mode)

    response = requests.post(
        f"{_api_base()}/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    if not response.ok:
        logger.error(
            "PayPal: błąd autoryzacji OAuth2 — HTTP %d: %s",
            response.status_code, response.text[:300],
        )
    response.raise_for_status()
    logger.debug("PayPal: access_token uzyskany pomyślnie")
    return response.json()["access_token"]


def create_order(amount_pln: str, points: int, user_email: str) -> dict:
    """
    Tworzy zamówienie PayPal (intent=CAPTURE).
    Zwraca pełną odpowiedź JSON, w tym order['id'].
    """
    token = _get_access_token()
    request_id = str(uuid.uuid4())
    logger.info(
        "PayPal create_order: %.2f PLN / %d pkt dla %s (request_id=%s)",
        float(amount_pln), points, user_email, request_id,
    )
    response = requests.post(
        f"{_api_base()}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": request_id,
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
    if not response.ok:
        logger.error(
            "PayPal create_order: błąd HTTP %d: %s",
            response.status_code, response.text[:300],
        )
    response.raise_for_status()
    order_id = response.json().get("id")
    logger.info("PayPal create_order: sukces, order_id=%s", order_id)
    return response.json()


def capture_order(order_id: str) -> dict:
    """
    Przechwytuje (finalizuje) zatwierdzone zamówienie PayPal.
    Zwraca pełną odpowiedź JSON; status='COMPLETED' oznacza sukces.
    """
    token = _get_access_token()
    logger.info("PayPal capture_order: order_id=%s", order_id)
    response = requests.post(
        f"{_api_base()}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": str(uuid.uuid4()),
        },
        timeout=15,
    )
    if not response.ok:
        logger.error(
            "PayPal capture_order [%s]: błąd HTTP %d: %s",
            order_id, response.status_code, response.text[:300],
        )
    response.raise_for_status()
    result = response.json()
    logger.info("PayPal capture_order [%s]: status=%s", order_id, result.get("status"))
    return result
