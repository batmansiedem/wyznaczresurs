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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statystyki globalne dla dashboardu admina."""
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

        return Response({
            'total_users': total_users,
            'active_this_month': active_this_month,
            'new_this_month': new_this_month,
            'total_transactions': total_transactions,
            'transactions_this_month': transactions_this_month,
            'total_revenue': float(revenue),
            'revenue_this_month': float(revenue_this_month),
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
            data.append({
                'id': r.id,
                'calculator_name': r.calculator_definition.name,
                'calculator_slug': r.calculator_definition.slug,
                'user_email': r.user.email,
                'user_id': r.user_id,
                'user_display': str(r.user),
                'is_locked': r.is_locked,
                'created_at': r.created_at.isoformat(),
            })
        return Response(data)
