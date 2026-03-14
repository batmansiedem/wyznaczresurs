from decimal import Decimal
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import CalculatorDefinition, CalculatorResult, Unit
from .serializers import CalculatorDefinitionSerializer, CalculatorResultSerializer, UnitSerializer
from .utils import convert_unit
from . import calculation_logic
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied


def _decimals_to_float(obj):
    """Rekurencyjnie konwertuje wartości Decimal na float dla serializacji JSON."""
    if isinstance(obj, dict):
        return {k: _decimals_to_float(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


class CalculatorDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows CalculatorDefinitions to be viewed.
    """
    queryset = CalculatorDefinition.objects.filter(is_active=True)
    serializer_class = CalculatorDefinitionSerializer
    lookup_field = 'slug' # Use slug for lookup instead of pk

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def calculate(self, request, slug=None):
        calculator_definition = self.get_object()
        user = request.user
        input_data = request.data.get('input_data')

        if not input_data:
            raise DRFValidationError("Brak danych wejściowych do obliczeń.")

        cost = calculator_definition.premium_cost
        has_points = user.is_superuser or cost == 0 or user.premium >= cost

        try:
            calculator_instance = calculation_logic.CalculatorFactory.get_calculator(slug, input_data)
            output_data = _decimals_to_float(calculator_instance.calculate())

            with transaction.atomic():
                if has_points and cost > 0 and not user.is_superuser:
                    user.premium -= cost
                    user.save()

                result = CalculatorResult.objects.create(
                    calculator_definition=calculator_definition,
                    user=user,
                    input_data=input_data,
                    output_data=output_data,
                    is_locked=not has_points,
                )

            if has_points:
                return Response({
                    "message": "Obliczenia wykonane pomyślnie.",
                    "output_data": output_data,
                    "remaining_premium": float(user.premium),
                    "result_id": result.id,
                    "is_locked": False,
                })
            else:
                return Response({
                    "is_locked": True,
                    "result_id": result.id,
                    "premium_cost": float(cost),
                    "remaining_premium": float(user.premium),
                    "message": "Brak wystarczającej liczby punktów premium. Odblokuj wynik.",
                })

        except DjangoValidationError as e:
            raise DRFValidationError(e.messages[0] if e.messages else str(e))
        except Exception as e:
            raise DRFValidationError(f"Wystąpił błąd podczas obliczeń: {e}")

class UnitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Units to be viewed.
    """
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    lookup_field = 'symbol'

class CalculatorResultViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Wyniki obliczeń — tylko odczyt i usuwanie (tworzenie przez endpoint /calculate)."""
    serializer_class = CalculatorResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CalculatorResult.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("Nie masz uprawnień do usunięcia tego wyniku.")
        instance.delete()

    @action(detail=False, methods=['get'])
    def for_calculator(self, request):
        """Zwraca wyniki dla konkretnego kalkulatora (slug przekazywany jako query param)."""
        slug = request.query_params.get('slug')
        if not slug:
            raise DRFValidationError("Parametr 'slug' jest wymagany.")
        calculator_definition = get_object_or_404(CalculatorDefinition, slug=slug)
        queryset = self.get_queryset().filter(calculator_definition=calculator_definition)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='unlock')
    def unlock(self, request, pk=None):
        """Odblokowanie zablokowanego wyniku za punkty premium."""
        result = self.get_object()
        if not result.is_locked:
            return Response({"detail": "Wynik nie jest zablokowany."})
        user = request.user
        cost = result.calculator_definition.premium_cost
        if not user.is_superuser and user.premium < cost:
            raise DRFValidationError(
                f"Brak wystarczającej liczby punktów premium (potrzeba {float(cost)}, masz {float(user.premium)})."
            )
        with transaction.atomic():
            if not user.is_superuser and cost > 0:
                user.premium -= cost
                user.save()
            result.is_locked = False
            result.save(update_fields=['is_locked'])
        return Response({
            "message": "Wyniki odblokowane pomyślnie.",
            "output_data": result.output_data,
            "remaining_premium": float(user.premium),
            "is_locked": False,
        })

    @action(detail=True, methods=['post'], url_path='copy_to')
    def copy_to(self, request, pk=None):
        """Admin kopiuje wynik obliczeń do innego użytkownika (lub do siebie)."""
        if not request.user.is_staff:
            raise PermissionDenied("Tylko administrator może kopiować obliczenia.")

        try:
            source = CalculatorResult.objects.get(pk=pk)
        except CalculatorResult.DoesNotExist:
            return Response({'detail': 'Nie znaleziono obliczenia.'}, status=status.HTTP_404_NOT_FOUND)

        target_user_id = request.data.get('target_user_id')
        if target_user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                target_user = User.objects.get(id=target_user_id)
            except User.DoesNotExist:
                return Response({'detail': 'Nie znaleziono użytkownika.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            target_user = request.user

        new_result = CalculatorResult.objects.create(
            calculator_definition=source.calculator_definition,
            user=target_user,
            input_data=source.input_data,
            output_data=source.output_data,
            is_locked=False,
        )
        return Response(CalculatorResultSerializer(new_result).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf_report(self, request, pk=None):
        """Generuje raport PDF dla danego wyniku obliczeń."""
        from django.http import HttpResponse
        from .pdf_generator import generate_result_pdf
        from users.models import UserLogo, UserSignature

        result = self.get_object()
        if result.is_locked:
            raise PermissionDenied("Odblokuj wyniki, aby pobrać PDF.")
        
        logo_id = request.query_params.get('logo_id')
        logo_obj = None
        if logo_id:
            try:
                logo_obj = UserLogo.objects.get(id=logo_id, user=request.user)
            except UserLogo.DoesNotExist:
                pass

        signature_id = request.query_params.get('signature_id')
        signature_obj = None
        if signature_id:
            try:
                signature_obj = UserSignature.objects.get(id=signature_id, user=request.user)
            except UserSignature.DoesNotExist:
                pass
        
        calculator_name = result.calculator_definition.name
        pdf_bytes = generate_result_pdf(result, calculator_name, logo_obj=logo_obj, signature_obj=signature_obj)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        slug = result.calculator_definition.slug
        response['Content-Disposition'] = f'attachment; filename="resurs_{slug}_{result.id}.pdf"'
        return response
