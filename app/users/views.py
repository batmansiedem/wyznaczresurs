from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def set_csrf_token(request):
    """
    To wywołanie wymusza na Django ustawienie ciasteczka 'csrftoken'.
    Jest niezbędne dla SPA (Quasar) przed próbą logowania.
    """
    return JsonResponse({'message': 'CSRF cookie set'})