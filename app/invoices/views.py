import datetime
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Invoice, PayPalOrder, PAYPAL_PACKAGES
from .serializers import InvoiceSerializer, CreateInvoiceSerializer, UserSimpleSerializer
from .pdf_generator import generate_invoice_pdf
from .paypal_client import create_order as paypal_create_order, capture_order as paypal_capture_order
from .ksef_service import submit as ksef_submit

User = get_user_model()


def _invoice_number() -> str:
    now = datetime.datetime.now()
    return f"FV/{now.year}/{now.month:02d}/{str(uuid.uuid4())[:8].upper()}"


def _buyer_data(user) -> dict:
    """Snapshot danych nabywcy z profilu użytkownika."""
    name = user.company_name or f"{user.first_name} {user.last_name}".strip() or user.email
    parts = [p for p in [user.address_line, f"{user.postal_code} {user.city}".strip()] if p]
    return {
        "buyer_name": name,
        "buyer_nip": user.nip or "",
        "buyer_address": ", ".join(parts),
    }


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            qs = Invoice.objects.all()
            user_id = self.request.query_params.get("user_id")
            if user_id:
                qs = qs.filter(user_id=user_id)
            return qs
        # Zwykły użytkownik — wszystkie faktury (z widocznym statusem KSeF)
        return Invoice.objects.filter(user=self.request.user)

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        if invoice.ksef_status != "accepted":
            return Response(
                {"detail": "PDF dostępny dopiero po akceptacji przez KSeF."},
                status=status.HTTP_403_FORBIDDEN,
            )
        pdf_content = generate_invoice_pdf(invoice)
        response = HttpResponse(pdf_content, content_type="application/pdf")
        filename = f"Faktura_{invoice.invoice_number.replace('/', '_')}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Ręczne wystawianie faktury przez admina (natychmiastowa akceptacja KSeF)."""
        if not request.user.is_staff:
            return Response({"detail": "Brak uprawnień."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target_user = User.objects.get(id=data["user_id"])
        net = data["net_amount"]
        vat = (net * Decimal("0.23")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross = net + vat

        buyer = _buyer_data(target_user)
        invoice = Invoice.objects.create(
            user=target_user,
            invoice_number=_invoice_number(),
            net_amount=net,
            vat_amount=vat,
            gross_amount=gross,
            points_added=data["points_to_add"],
            ksef_status="pending",
            buyer_name=data.get("buyer_name") or buyer["buyer_name"],
            buyer_nip=data.get("buyer_nip") or buyer["buyer_nip"],
            buyer_address=data.get("buyer_address") or buyer["buyer_address"],
        )

        # Admin wystawia fakturę → automatyczna akceptacja KSeF + doładowanie punktów
        ksef_submit(invoice)

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# PayPal
# ---------------------------------------------------------------------------

class PayPalCreateOrderView(views.APIView):
    """
    POST /api/billing/paypal/create-order/
    Body: { "package": "100" | "250" | "500" | "1000" }
    Tworzy zamówienie PayPal i zwraca order_id do JS SDK.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        package_key = str(request.data.get("package", ""))

        if package_key == "custom":
            try:
                points = int(request.data.get("points", 0))
            except (TypeError, ValueError):
                points = 0
            if not (50 <= points <= 9999):
                return Response(
                    {"detail": "Podaj liczbę punktów od 50 do 9999."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            pkg = {"points": points, "gross": Decimal(str(points))}  # 1 PLN = 1 pkt
        elif package_key in PAYPAL_PACKAGES:
            pkg = PAYPAL_PACKAGES[package_key]
        else:
            return Response(
                {"detail": f"Nieprawidłowy pakiet. Dostępne: {list(PAYPAL_PACKAGES)} lub 'custom'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order_data = paypal_create_order(
                str(pkg["gross"]), pkg["points"], request.user.email
            )
        except Exception as e:
            return Response(
                {"detail": f"Błąd komunikacji z PayPal: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        PayPalOrder.objects.create(
            paypal_order_id=order_data["id"],
            amount=pkg["gross"],
            points=pkg["points"],
            user=request.user,
        )

        return Response({"order_id": order_data["id"]})


class PayPalCaptureOrderView(views.APIView):
    """
    POST /api/billing/paypal/capture-order/<order_id>/
    Przechwytuje płatność, wystawia fakturę i przesyła do KSeF (mock).
    Zwraca gotową fakturę z ksef_status='accepted'.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id):
        try:
            paypal_order = PayPalOrder.objects.select_for_update().get(
                paypal_order_id=order_id,
                user=request.user,
            )
        except PayPalOrder.DoesNotExist:
            return Response({"detail": "Zamówienie nie istnieje."}, status=status.HTTP_404_NOT_FOUND)

        if paypal_order.status != "created":
            return Response(
                {"detail": "Zamówienie zostało już przetworzone."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Przechwycenie płatności przez PayPal
        try:
            capture_data = paypal_capture_order(order_id)
        except Exception as e:
            paypal_order.status = "failed"
            paypal_order.save()
            return Response(
                {"detail": f"Błąd PayPal podczas przechwycenia: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if capture_data.get("status") != "COMPLETED":
            paypal_order.status = "failed"
            paypal_order.save()
            return Response(
                {"detail": "Płatność nie została potwierdzona przez PayPal."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obliczenie kwot (brutto znane → odlicz VAT 23%)
        gross = paypal_order.amount
        net = (gross / Decimal("1.23")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        vat = gross - net

        buyer = _buyer_data(request.user)
        invoice = Invoice.objects.create(
            user=request.user,
            invoice_number=_invoice_number(),
            net_amount=net,
            vat_amount=vat,
            gross_amount=gross,
            points_added=paypal_order.points,
            ksef_status="pending",   # ← jeszcze nie zaakceptowana
            **buyer,
        )

        paypal_order.status = "completed"
        paypal_order.invoice = invoice
        paypal_order.save()

        # Wysyłka do KSeF (mock): pending → sent → accepted + doładowanie punktów
        ksef_submit(invoice)

        return Response({"invoice": InvoiceSerializer(invoice).data})


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

class AdminUserListView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("email")
        return Response(UserSimpleSerializer(users, many=True).data)


class AdminInvoiceReportView(views.APIView):
    """
    GET /api/billing/admin/report/?year=2026&month=02
    Zestawienie faktur z okresu dla admina.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.db.models import Sum, Count

        qs = Invoice.objects.select_related("user").all()

        year       = request.query_params.get("year")
        month      = request.query_params.get("month")
        user_id    = request.query_params.get("user_id")
        ksef_status = request.query_params.get("ksef_status")

        if year:       qs = qs.filter(issue_date__year=year)
        if month:      qs = qs.filter(issue_date__month=month)
        if user_id:    qs = qs.filter(user_id=user_id)
        if ksef_status: qs = qs.filter(ksef_status=ksef_status)

        totals = qs.aggregate(
            total_net=Sum("net_amount"),
            total_vat=Sum("vat_amount"),
            total_gross=Sum("gross_amount"),
            total_points=Sum("points_added"),
            count=Count("id"),
        )

        return Response({
            "invoices": InvoiceSerializer(qs.order_by("issue_date"), many=True).data,
            "summary": {
                "count":       totals["count"] or 0,
                "total_net":   float(totals["total_net"] or 0),
                "total_vat":   float(totals["total_vat"] or 0),
                "total_gross": float(totals["total_gross"] or 0),
                "total_points": totals["total_points"] or 0,
            },
            "filters": {
                "year": year, "month": month,
                "user_id": user_id, "ksef_status": ksef_status,
            },
        })
