from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Nadpisuje domyślny adapter allauth.
    Główna zmiana: link potwierdzający email kieruje na frontend SPA,
    nie na backend Django.
    """

    def get_email_confirmation_url(self, request, emailconfirmation):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
        return f"{frontend_url}/confirm-email/{emailconfirmation.key}"
