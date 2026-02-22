from django.urls import path, include
from .views import set_csrf_token

urlpatterns = [
    # Nasz endpoint pomocniczy
    path('csrf/', set_csrf_token, name='csrf'),

    # Gotowe widoki z biblioteki (Login, Logout, Password Reset, Refresh)
    path('', include('dj_rest_auth.urls')),

    # Rejestracja
    path('registration/', include('dj_rest_auth.registration.urls')),
]