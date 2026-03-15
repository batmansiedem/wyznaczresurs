from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvoiceViewSet,
    AdminUserListView,
    AdminInvoiceReportView,
    PayPalCreateOrderView,
    PayPalCaptureOrderView,
    PublicConfigView,
    BonusRedeemView,
)

router = DefaultRouter()
router.register(r"invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("", include(router.urls)),
    path("public-config/", PublicConfigView.as_view(), name="public-config"),
    path("redeem-code/", BonusRedeemView.as_view(), name="redeem-code"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/report/", AdminInvoiceReportView.as_view(), name="admin-invoice-report"),
    # PayPal
    path("paypal/create-order/", PayPalCreateOrderView.as_view(), name="paypal-create-order"),
    path("paypal/capture-order/<str:order_id>/", PayPalCaptureOrderView.as_view(), name="paypal-capture-order"),
]
