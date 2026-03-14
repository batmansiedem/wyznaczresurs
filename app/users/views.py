import secrets
import string
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count, Q, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from calculators.models import CalculatorResult
from calculators.serializers import CalculatorResultSerializer
from .serializers import (
    AdminUserListSerializer,
    AdminUpdateUserSerializer,
    AdminCreateUserSerializer,
)

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def set_csrf_token(request):
    """
    Wymusza ustawienie ciasteczka 'csrftoken' przez Django.
    Niezbędne dla SPA przed próbą logowania.
    """
    return JsonResponse({'message': 'CSRF cookie set'})


from rest_framework import permissions, parsers
from .models import UserLogo, UserSignature
from .serializers import (
    AdminUserListSerializer,
    AdminUpdateUserSerializer,
    AdminCreateUserSerializer,
    UserLogoSerializer,
    UserSignatureSerializer,
)

User = get_user_model()

class UserLogoViewSet(viewsets.ModelViewSet):
    """Widok do zarządzania logotypami użytkownika."""
    serializer_class = UserLogoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        return UserLogo.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')

    def create(self, request, *args, **kwargs):
        user = request.user
        cost = 200
        
        if user.premium < cost:
            return Response(
                {"detail": f"Niewystarczająca liczba punktów premium (wymagane {cost} pkt)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user.premium -= cost
        user.has_custom_logo = True
        user.save()
        
        # Jeśli to pierwsze logo, ustaw jako domyślne
        is_first = not UserLogo.objects.filter(user=user).exists()
        logo = serializer.save(user=user, is_default=is_first)
        
        # Synchronizacja z "starymi" polami w CustomUser dla wstecznej kompatybilności
        if is_first or logo.is_default:
            user.custom_logo = logo.image
            user.logo_width = logo.width
            user.logo_height = logo.height
            user.logo_position = logo.position
            user.theme_color = logo.theme_color
            user.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        logo = serializer.save()
        user = self.request.user
        # Jeśli edytowane logo jest domyślne, zaktualizuj też pola w CustomUser
        if logo.is_default:
            user.custom_logo = logo.image
            user.logo_width = logo.width
            user.logo_height = logo.height
            user.logo_position = logo.position
            user.theme_color = logo.theme_color
            user.save()

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        logo = self.get_object()
        logo.is_default = True
        logo.save()
        
        # Aktualizacja CustomUser
        user = request.user
        user.custom_logo = logo.image
        user.logo_width = logo.width
        user.logo_height = logo.height
        user.logo_position = logo.position
        user.theme_color = logo.theme_color
        user.save()
        
        return Response({"message": "Logo ustawione jako domyślne."})

class UserSignatureViewSet(viewsets.ModelViewSet):
    """Widok do zarządzania podpisami użytkownika."""
    serializer_class = UserSignatureSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        return UserSignature.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Podpisy są obecnie darmowe
        is_first = not UserSignature.objects.filter(user=user).exists()
        serializer.save(user=user, is_default=is_first)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        signature = self.get_object()
        signature.is_default = True
        signature.save()
        return Response({"message": "Podpis ustawiony jako domyślny."})

class PurchaseCustomLogoView(APIView):
    """Zakup własnego loga na obliczeniach za 200 pkt."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.has_custom_logo:
            return Response({"detail": "Już posiadasz wykupione własne logo."}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.premium < 200:
            return Response({"detail": "Niewystarczająca liczba punktów premium (wymagane 200 pkt)."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.premium -= 200
        user.has_custom_logo = True
        user.save()
        
        return Response({
            "message": "Pomyślnie wykupiono własne logo na obliczeniach!",
            "premium": user.premium,
            "has_custom_logo": user.has_custom_logo
        })

class UserLogoUploadView(APIView):
    """Upload pliku loga (tylko jeśli wykupione)."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        user = request.user
        if not user.has_custom_logo:
            return Response({"detail": "Musisz najpierw wykupić opcję własnego loga."}, status=status.HTTP_403_FORBIDDEN)
        
        logo_file = request.data.get('custom_logo')
        if not logo_file:
            return Response({"detail": "Nie przesłano pliku loga."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.custom_logo = logo_file
        user.save()
        
        # Zwróć pełną ścieżkę do loga
        logo_url = request.build_absolute_uri(user.custom_logo.url) if user.custom_logo else None
        return Response({
            "message": "Logo zostało pomyślnie zaktualizowane.",
            "custom_logo_url": logo_url
        })

class LogoPreviewView(APIView):
    """Generuje przykładowy dokument PDF z logiem użytkownika."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        logo_id = request.query_params.get('logo_id')
        
        # Pobierz konkretne logo lub domyślne
        logo_obj = None
        if logo_id:
            try:
                logo_obj = UserLogo.objects.get(id=logo_id, user=user)
            except UserLogo.DoesNotExist:
                pass
        
        if not logo_obj:
            logo_obj = UserLogo.objects.filter(user=user, is_default=True).first()
            if not logo_obj and user.has_custom_logo:
                # Fallback do pól w CustomUser jeśli brak modelu UserLogo (nie powinno się zdarzyć po migracji)
                pass

        from calculators.pdf_generator import generate_result_pdf
        from calculators.models import CalculatorResult
        import datetime

        # Tworzymy tymczasowy, wirtualny wynik do celów podglądu
        mock_result = CalculatorResult(
            user=user,
            created_at=datetime.datetime.now(),
            input_data={
                "nr_fabryczny": "PRZYKŁAD-123",
                "producent": "TWOJA FIRMA",
                "typ": "Urządzenie podlegające UDT",
                "ilosc_cykli": 12500
            },
            output_data={
                "resurs_wykorzystanie": 45.5,
                "resurs_message": "Urządzenie zdolne do dalszej eksploatacji."
            }
        )
        # Przekazujemy atrybuty użytkownika/loga do mocka
        mock_result.user.has_custom_logo = True if logo_obj else user.has_custom_logo
        if logo_obj:
            mock_result.user.custom_logo = logo_obj.image
            mock_result.user.logo_width = logo_obj.width
            mock_result.user.logo_height = logo_obj.height
            mock_result.user.logo_position = logo_obj.position
            mock_result.user.theme_color = logo_obj.theme_color
        else:
            mock_result.user.custom_logo = user.custom_logo
            mock_result.user.logo_width = user.logo_width
            mock_result.user.logo_height = user.logo_height
            mock_result.user.logo_position = user.logo_position
            mock_result.user.theme_color = user.theme_color
        
        from django.http import HttpResponse
        pdf_content = generate_result_pdf(mock_result, "Kalkulator Przykładowy", logo_obj=logo_obj)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="przyklad_logo.pdf"'
        return response

class SignaturePreviewView(APIView):
    """Generuje przykładowy dokument PDF z podpisem użytkownika."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        signature_id = request.query_params.get('signature_id')
        
        # Pobierz konkretny podpis lub domyślny
        signature_obj = None
        if signature_id:
            try:
                signature_obj = UserSignature.objects.get(id=signature_id, user=user)
            except UserSignature.DoesNotExist:
                pass
        
        if not signature_obj:
            signature_obj = UserSignature.objects.filter(user=user, is_default=True).first()

        from calculators.pdf_generator import generate_result_pdf
        from calculators.models import CalculatorResult
        import datetime

        # Tworzymy tymczasowy, wirtualny wynik do celów podglądu
        mock_result = CalculatorResult(
            user=user,
            created_at=datetime.datetime.now(),
            input_data={
                "nr_fabryczny": "PRZYKŁAD-PODPIS",
                "producent": "TWOJA FIRMA",
                "typ": "Urządzenie podlegające UDT",
            },
            output_data={
                "resurs_wykorzystanie": 10.0,
                "resurs_message": "Podgląd rozmieszczenia podpisu."
            }
        )
        
        from django.http import HttpResponse
        # Uwaga: Muszę zaktualizować generate_result_pdf, aby przyjmował signature_obj
        pdf_content = generate_result_pdf(mock_result, "Kalkulator Przykładowy", signature_obj=signature_obj)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="przyklad_podpis.pdf"'
        return response

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    CRUD użytkowników dla superadmina.
    """
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminCreateUserSerializer
        if self.action == 'partial_update':
            return AdminUpdateUserSerializer
        return AdminUserListSerializer

    def _annotated_qs(self):
        return User.objects.annotate(
            transaction_count=Count('calculator_results', distinct=True),
            invoice_count=Count('invoices', distinct=True),
        )

    def get_queryset(self):
        qs = self._annotated_qs().order_by('-date_joined')

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(company_name__icontains=search) |
                Q(nip__icontains=search)
            )
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() == 'true'))
        is_company = self.request.query_params.get('is_company')
        if is_company is not None:
            qs = qs.filter(is_company=(is_company.lower() == 'true'))

        return qs

    def create(self, request, *args, **kwargs):
        serializer = AdminCreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        password = data.get('password') or ''.join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
        )

        user = User.objects.create_user(
            email=data['email'],
            password=password,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            is_company=data.get('is_company', False),
            company_name=data.get('company_name', ''),
            nip=data.get('nip', ''),
            address_line=data.get('address_line', ''),
            postal_code=data.get('postal_code', ''),
            city=data.get('city', ''),
            premium=data.get('premium', 0),
        )

        obj = self._annotated_qs().get(pk=user.pk)
        return Response(AdminUserListSerializer(obj).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = AdminUpdateUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        obj = self._annotated_qs().get(pk=user.pk)
        return Response(AdminUserListSerializer(obj).data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "Nie możesz usunąć własnego konta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Transakcje (wyniki kalkulatorów) wybranego użytkownika."""
        user = self.get_object()
        qs = user.calculator_results.select_related('calculator_definition').all()

        year = request.query_params.get('year')
        month = request.query_params.get('month')
        search = request.query_params.get('search', '').strip()
        if year:
            qs = qs.filter(created_at__year=year)
        if month:
            qs = qs.filter(created_at__month=month)
        if search:
            qs = qs.filter(calculator_definition__name__icontains=search)

        serializer = CalculatorResultSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def logos(self, request, pk=None):
        """Zarządzanie logotypami wybranego użytkownika przez admina."""
        user = self.get_object()
        
        if request.method == 'POST':
            serializer = UserLogoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Admin dodaje logo za darmo (nie pobieramy punktów)
            logo = serializer.save(user=user)
            
            # Synchronizacja z "starymi" polami w CustomUser jeśli to domyślne lub pierwsze logo
            is_first = user.logos.count() == 1
            if is_first or logo.is_default:
                user.has_custom_logo = True
                user.custom_logo = logo.image
                user.logo_width = logo.width
                user.logo_height = logo.height
                user.logo_position = logo.position
                user.theme_color = logo.theme_color
                user.save()
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # GET: Zwraca listę logotypów
        logos = user.logos.all().order_by('-is_default', '-created_at')
        serializer = UserLogoSerializer(logos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def signatures(self, request, pk=None):
        """Zarządzanie podpisami wybranego użytkownika przez admina."""
        user = self.get_object()
        
        if request.method == 'POST':
            serializer = UserSignatureSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Admin dodaje podpis za darmo
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # GET: Zwraca listę podpisów
        sigs = user.signatures.all().order_by('-is_default', '-created_at')
        serializer = UserSignatureSerializer(sigs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statystyki globalne oraz trendy miesięczne dla dashboardu admina."""
        # Import wewnątrz metody — unika circular imports
        from invoices.models import Invoice  # noqa

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_users = User.objects.count()
        active_this_month = User.objects.filter(last_login__gte=month_start).count()
        new_this_month = User.objects.filter(date_joined__gte=month_start).count()
        total_transactions = CalculatorResult.objects.count()
        transactions_this_month = CalculatorResult.objects.filter(created_at__gte=month_start).count()
        revenue = Invoice.objects.aggregate(total=Sum('gross_amount'))['total'] or 0
        revenue_this_month = (
            Invoice.objects
            .filter(created_at__gte=month_start)
            .aggregate(total=Sum('gross_amount'))['total'] or 0
        )

        # TRENDY (Ostatnie 6 miesięcy)
        monthly_trends = []
        for i in range(5, -1, -1):
            # Obliczanie pierwszego dnia miesiąca sprzed i miesięcy
            # month_start_date: 1-szy dzień obecnego miesiąca
            # target_month: month_start_date minus i miesięcy
            
            # Prosta, bezpieczna arytmetyka miesięcy
            target_year = now.year
            target_month = now.month - i
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            start = timezone.datetime(target_year, target_month, 1, tzinfo=timezone.get_current_timezone())
            
            # Koniec miesiąca (początek następnego)
            end_month = target_month + 1
            end_year = target_year
            if end_month > 12:
                end_month = 1
                end_year += 1
            end = timezone.datetime(end_year, end_month, 1, tzinfo=timezone.get_current_timezone())

            new_u = User.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
            txs = CalculatorResult.objects.filter(created_at__gte=start, created_at__lt=end).count()
            # Używamy gross_amount dla przychodów brutto
            rev = Invoice.objects.filter(created_at__gte=start, created_at__lt=end, is_proforma=False).aggregate(total=Sum('gross_amount'))['total'] or 0
            
            monthly_trends.append({
                'label': start.strftime('%m/%Y'),
                'users': new_u,
                'transactions': txs,
                'revenue': float(rev),
            })

        return Response({
            'total_users': total_users,
            'active_this_month': active_this_month,
            'new_this_month': new_this_month,
            'total_transactions': total_transactions,
            'transactions_this_month': transactions_this_month,
            'total_revenue': float(revenue),
            'revenue_this_month': float(revenue_this_month),
            'monthly_trends': monthly_trends,
        })


class AdminAllTransactionsView(APIView):
    """
    Wszystkie transakcje z filtrowaniem — dla admina.
    GET /api/admin/transactions/?year=&month=&search=&user_id=
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = CalculatorResult.objects.select_related(
            'calculator_definition', 'user'
        ).order_by('-created_at')

        year = request.query_params.get('year')
        month = request.query_params.get('month')
        search = request.query_params.get('search', '').strip()
        user_id = request.query_params.get('user_id')

        if year:
            qs = qs.filter(created_at__year=year)
        if month:
            qs = qs.filter(created_at__month=month)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if search:
            qs = qs.filter(
                Q(calculator_definition__name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__company_name__icontains=search)
            )

        data = []
        for r in qs[:500]:
            # Wyciągnij nr_fabryczny i typ z input_data (JSON)
            input_d = r.input_data or {}
            nr_fab = input_d.get('nr_fabryczny', '')
            # Jeśli to obiekt {value, unit}, weź .value
            if isinstance(nr_fab, dict):
                nr_fab = nr_fab.get('value', '')
            
            typ_val = input_d.get('typ', '')
            if isinstance(typ_val, dict):
                typ_val = typ_val.get('value', '')

            data.append({
                'id': r.id,
                'calculator_name': r.calculator_definition.name,
                'calculator_slug': r.calculator_definition.slug,
                'user_email': r.user.email,
                'user_id': r.user_id,
                'user_display': str(r.user),
                'is_locked': r.is_locked,
                'created_at': r.created_at.isoformat(),
                'nr_fabryczny': nr_fab,
                'typ': typ_val,
            })
        return Response(data)
