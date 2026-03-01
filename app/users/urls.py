from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import set_csrf_token, AdminUserViewSet, AdminAllTransactionsView

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    # Endpoint pomocniczy — CSRF
    path('csrf/', set_csrf_token, name='csrf'),

    # Gotowe widoki biblioteki (Login, Logout, Password Reset, Refresh)
    path('', include('dj_rest_auth.urls')),

    # Rejestracja
    path('registration/', include('dj_rest_auth.registration.urls')),

    # Panel administratora
    path('', include(router.urls)),
    path('admin/transactions/', AdminAllTransactionsView.as_view(), name='admin-transactions'),
]
