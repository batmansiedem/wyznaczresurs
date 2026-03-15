from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import random
import string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import SendEmailSerializer
from invoices.models import BonusPointsCode

User = get_user_model()

def generate_random_code(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class SendNotificationEmailView(APIView):
    """
    API endpoint dla administratorów do wysyłania e-maili do wszystkich lub wybranych użytkowników.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = SendEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        subject = serializer.validated_data['subject']
        raw_content = serializer.validated_data['content']
        all_users = serializer.validated_data.get('all_users', False)
        user_ids = serializer.validated_data.get('user_ids', [])
        
        include_bonus_code = serializer.validated_data.get('include_bonus_code', False)
        bonus_points = serializer.validated_data.get('bonus_points', 0)

        # Wybierz odbiorców
        if all_users:
            recipients = User.objects.filter(is_active=True).values_list('email', flat=True)
        elif user_ids:
            recipients = User.objects.filter(id__in=user_ids, is_active=True).values_list('email', flat=True)
        else:
            return Response({"detail": "Musisz wybrać odbiorców lub zaznaczyć opcję 'Wszyscy'."}, status=status.HTTP_400_BAD_REQUEST)

        if not recipients:
            return Response({"detail": "Brak aktywnych odbiorców spełniających kryteria."}, status=status.HTTP_404_NOT_FOUND)

        count = 0
        errors = []

        # Wysyłaj e-maile
        for email in recipients:
            try:
                # Generuj kod jeśli zaznaczono opcję
                current_bonus_code = None
                if include_bonus_code and bonus_points > 0:
                    code_str = generate_random_code()
                    current_bonus_code = BonusPointsCode.objects.create(
                        code=code_str,
                        points=bonus_points
                    )

                # Przygotuj treść HTML na podstawie szablonu (dla każdego odbiorcy osobno jeśli mamy kody)
                context = {
                    'subject': subject,
                    'content': raw_content,
                    'year': timezone.now().year,
                    'bonus_code': current_bonus_code.code if current_bonus_code else None,
                    'bonus_points': bonus_points if current_bonus_code else None
                }
                html_content = render_to_string('notifications/email_template.html', context)
                text_content = strip_tags(html_content)

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                count += 1
            except Exception as e:
                errors.append(f"Błąd przy wysyłce do {email}: {str(e)}")

        response_data = {
            "detail": f"Wysłano pomyślnie do {count} odbiorców.",
            "success_count": count,
            "error_count": len(errors),
            "errors": errors if errors else None
        }

        return Response(response_data, status=status.HTTP_200_OK if count > 0 else status.HTTP_500_INTERNAL_SERVER_ERROR)

class UsersListView(APIView):
    """
    Zwraca uproszczoną listę użytkowników do wyboru w formularzu wysyłki.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.filter(is_active=True).order_by('email')
        data = []
        for u in users:
            name = ""
            if u.is_company:
                name = u.company_name or ""
            else:
                name = f"{u.first_name} {u.last_name}".strip()
            
            data.append({
                "id": u.id,
                "email": u.email,
                "is_company": u.is_company,
                "display_name": f"{name} ({u.email})" if name else u.email
            })
        return Response(data)
