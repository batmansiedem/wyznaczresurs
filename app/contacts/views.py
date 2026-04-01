from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings

from .serializers import ContactFormSerializer

from rest_framework.permissions import AllowAny

class ContactFormView(APIView):
    """
    API endpoint for handling contact form submissions.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ContactFormSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            validated_data = serializer.validated_data
            
            # Construct the email details
            if user.is_authenticated:
                user_email = user.email
                user_name = f"{user.first_name} {user.last_name} ({user.company_name or 'Osoba prywatna'})"
            else:
                user_email = validated_data.get('email')
                user_name = validated_data.get('name')

            subject = validated_data.get('subject', 'Nowa wiadomość kontaktowa')
            phone = validated_data.get('phone', 'Nie podano')
            message_body = validated_data.get('message')

            full_message = (
                f"Nowa wiadomość z formularza kontaktowego:\n"
                f"------------------------------------------\n"
                f"Użytkownik: {user_email}\n"
                f"Nazwa: {user_name}\n"
                f"Telefon: {phone}\n"
                f"Temat: {subject}\n"
                f"------------------------------------------\n\n"
                f"Treść wiadomości:\n{message_body}"
            )

            try:
                send_mail(
                    subject=f"[Formularz Kontaktowy] {subject}",
                    message=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.SITEEMAIL],
                    fail_silently=False,
                )
                return Response({"detail": "Wiadomość została wysłana pomyślnie."}, status=status.HTTP_200_OK)
            except Exception as e:
                # Log error or return detail if needed
                return Response({"detail": f"Wystąpił błąd podczas wysyłania wiadomości: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
