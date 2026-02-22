import datetime
import uuid
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Invoice
from .serializers import InvoiceSerializer, CreateInvoiceSerializer, UserSimpleSerializer
from .pdf_generator import generate_invoice_pdf

User = get_user_model()

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Invoice.objects.all()
        return Invoice.objects.filter(user=self.request.user)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        pdf_content = generate_invoice_pdf(invoice)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"Faktura_{invoice.invoice_number.replace('/', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"detail": "Brak uprawnień."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CreateInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        target_user = User.objects.get(id=data['user_id'])
        
        net = data['net_amount']
        vat = net * Decimal('0.23')
        gross = net + vat
        
        # Prosty generator numeru faktury (np. FV/2026/02/RANDOM)
        now = datetime.datetime.now()
        unique_suffix = str(uuid.uuid4())[:8].upper()
        invoice_no = f"FV/{now.year}/{now.month:02d}/{unique_suffix}"
        
        # MOCK KSeF - symulacja wysyłki
        # W rzeczywistości tutaj byłoby wywołanie klienta KSeF (np. przez sesję interaktywną)
        ksef_ref = f"KSEF-{now.strftime('%Y%m%d')}-{unique_suffix}"
        
        invoice = Invoice.objects.create(
            user=target_user,
            invoice_number=invoice_no,
            net_amount=net,
            vat_amount=vat,
            gross_amount=gross,
            points_added=data['points_to_add'],
            ksef_reference_number=ksef_ref,
            ksef_status='accepted', # MOCK: od razu zaakceptowana w środowisku testowym
            buyer_name=data.get('buyer_name', target_user.company_name or f"{target_user.first_name} {target_user.last_name}"),
            buyer_nip=data.get('buyer_nip', target_user.nip or ""),
            buyer_address=data.get('buyer_address', f"{target_user.address_line}, {target_user.postal_code} {target_user.city}")
        )
        
        # Doładowanie punktów użytkownikowi
        target_user.premium += data['points_to_add']
        target_user.save()
        
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

class AdminUserListView(views.APIView):
    """Widok dla admina do pobrania listy użytkowników do selecta"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        users = User.objects.all().order_by('email')
        serializer = UserSimpleSerializer(users, many=True)
        return Response(serializer.data)
