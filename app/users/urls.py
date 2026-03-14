from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    set_csrf_token, AdminUserViewSet, AdminAllTransactionsView,
    PurchaseCustomLogoView, UserLogoUploadView, LogoPreviewView,
    UserLogoViewSet, UserSignatureViewSet, SignaturePreviewView
)

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')
router.register(r'logos', UserLogoViewSet, basename='user-logos')
router.register(r'signatures', UserSignatureViewSet, basename='user-signatures')

urlpatterns = [
    # Endpoint pomocniczy — CSRF
    path('csrf/', set_csrf_token, name='csrf'),

    # Własne logo
    path('purchase-custom-logo/', PurchaseCustomLogoView.as_view(), name='purchase-custom-logo'),
    path('upload-logo/', UserLogoUploadView.as_view(), name='upload-logo'),
    path('logo-preview/', LogoPreviewView.as_view(), name='logo-preview'),
    path('signature-preview/', SignaturePreviewView.as_view(), name='signature-preview'),

    # Gotowe widoki biblioteki (Login, Logout, Password Reset, Refresh)
    path('', include('dj_rest_auth.urls')),

    # Rejestracja
    path('registration/', include('dj_rest_auth.registration.urls')),

    # Panel administratora
    path('', include(router.urls)),
    path('admin/transactions/', AdminAllTransactionsView.as_view(), name='admin-transactions'),
]
