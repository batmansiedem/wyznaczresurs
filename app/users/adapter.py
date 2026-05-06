import logging
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

logger = logging.getLogger(__name__)

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Nadpisuje domyślny adapter allauth.
    Główna zmiana: link potwierdzający email kieruje na frontend SPA,
    nie na backend Django.
    """

    def get_email_confirmation_url(self, request, emailconfirmation):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
        url = f"{frontend_url}/confirm-email/{emailconfirmation.key}"
        logger.info(f"Generating email confirmation URL for {emailconfirmation.email_address.email}: {url}")
        return url

    def get_reset_password_from_key_url(self, key):
        """
        Nadpisujemy, aby uniknąć NoReverseMatch: 'account_reset_password_from_key'.
        Zwracamy cokolwiek, bo i tak poprawiamy to w send_mail mając dostęp do UID.
        """
        return f"placeholder-url-for-key-{key}"

    def send_mail(self, template_prefix, email, context):
        """
        Nadpisujemy send_mail aby logować próby wysyłki oraz poprawiać linki 
        dla SPA (np. reset hasła).
        """
        if template_prefix == 'account/email/password_reset_key':
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
            # context['password_reset_url'] to zwykle URL do backendu, 
            # zmieniamy na frontend: /password-reset/confirm/uid/token
            # allauth w kontekście resetu hasła podaje 'uid' i 'token' (lub 'key')
            # W dj-rest-auth używamy uid i token.
            uid = context.get('uid') or context.get('uidb64') or context.get('uidb36')
            token = context.get('token') or context.get('key')
            if uid and token:
                context['password_reset_url'] = f"{frontend_url}/password-reset/confirm/{uid}/{token}"
                logger.info(f"Fixed password reset URL for SPA: {context['password_reset_url']}")

        logger.info(f"Attempting to send allauth email: {template_prefix} to {email}")
        try:
            super().send_mail(template_prefix, email, context)
            logger.info(f"Successfully triggered allauth email: {template_prefix} to {email}")
        except Exception as e:
            logger.error(f"FAILED to send allauth email: {template_prefix} to {email}. Error: {str(e)}")
            raise e
