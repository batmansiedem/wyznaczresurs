import rest_framework.views
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import CalculatorDefinition, CalculatorResult, Unit
from .serializers import CalculatorDefinitionSerializer, CalculatorResultSerializer, UnitSerializer
from .utils import convert_unit, decimals_to_float
from . import calculation_logic
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied


class CalculatorDefinitionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows CalculatorDefinitions to be viewed and edited by admins.
    """
    queryset = CalculatorDefinition.objects.all()
    serializer_class = CalculatorDefinitionSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'update_prices']:
            return [IsAuthenticated(), rest_framework.permissions.IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, rest_framework.permissions.IsAdminUser])
    def update_prices(self, request):
        """Masowa aktualizacja cen kalkulatorów."""
        prices = request.data.get('prices', []) # List of {id, premium_cost, premium_cost_recurring}
        if not prices:
            return Response({"detail": "Brak danych."}, status=400)
        
        updated_count = 0
        with transaction.atomic():
            for p in prices:
                try:
                    calc = CalculatorDefinition.objects.get(id=p['id'])
                    calc.premium_cost = p['premium_cost']
                    calc.premium_cost_recurring = p['premium_cost_recurring']
                    calc.save()
                    updated_count += 1
                except (CalculatorDefinition.DoesNotExist, KeyError):
                    continue
        
        return Response({"detail": f"Zaktualizowano {updated_count} kalkulatorów."})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def schemas(self, request):
        """Zwraca konfiguracje wszystkich kalkulatorów (pola formularzy + pola wynikowe)."""
        from .device_config import get_all_configs
        return Response(get_all_configs())

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def schema(self, request, slug=None):
        """Zwraca konfigurację pojedynczego kalkulatora."""
        from .device_config import load_config
        config = load_config(slug)
        if not config:
            return Response({'detail': 'Konfiguracja nie znaleziona.'}, status=404)
        return Response(config)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def get_cost(self, request, slug=None):
        """Zwraca koszt obliczenia dla danego użytkownika i danych wejściowych."""
        calculator_definition = self.get_object()
        user = request.user
        input_data = request.data.get('input_data', {})
        
        cost = self._calculate_actual_cost(user, calculator_definition, input_data)
        return Response({
            "cost": float(cost),
            "user_premium": float(user.premium),
            "can_afford": user.is_superuser or user.premium >= cost
        })

    def _calculate_actual_cost(self, user, calculator_definition, input_data):
        """Pomocnicza metoda do wyliczania kosztu po zniżkach."""
        from decimal import Decimal
        
        is_recurring = input_data.get('ponowny_resurs') == 'Tak'
        base_cost = calculator_definition.premium_cost_recurring if is_recurring else calculator_definition.premium_cost
        
        # Zastosuj zniżkę procentową użytkownika
        if hasattr(user, 'discount_percent') and user.discount_percent > 0:
            actual_cost = base_cost * (Decimal(100 - user.discount_percent) / Decimal(100))
        else:
            actual_cost = base_cost
        
        return actual_cost.quantize(Decimal('0.01'))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def calculate(self, request, slug=None):
        calculator_definition = self.get_object()
        user = request.user
        input_data = request.data.get('input_data')

        if not input_data:
            raise DRFValidationError("Brak danych wejściowych do obliczeń.")

        cost = self._calculate_actual_cost(user, calculator_definition, input_data)
        has_points = user.is_superuser or cost == 0 or user.premium >= cost

        try:
            calculator_instance = calculation_logic.CalculatorFactory.get_calculator(slug, input_data)
            output_data = decimals_to_float(calculator_instance.calculate())

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
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Wyniki obliczeń — odczyt, aktualizacja i usuwanie."""
    serializer_class = CalculatorResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            CalculatorResult.objects
            .filter(user=self.request.user)
            .select_related('calculator_definition')
            .order_by('-created_at')
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user
        input_data = self.request.data.get('input_data')
        
        if not input_data:
            return # Standard serializer update if no input_data provided

        # 1. Sprawdź pola krytyczne: nr_fabryczny, lata_pracy
        def get_val(v):
            if isinstance(v, dict): return v.get('value')
            return v

        IMMUTABLE = ['nr_fabryczny', 'lata_pracy', 'data_resurs', 'ostatni_resurs']
        for field in IMMUTABLE:
            old_val = get_val(instance.input_data.get(field))
            new_val = get_val(input_data.get(field))
            if old_val != new_val:
                raise DRFValidationError(
                    f"Modyfikacja pola '{field}' wymaga utworzenia nowego resursu (użyj przycisku Oblicz)."
                )

        # 2. Modyfikacja istniejącego wyniku jest bezpłatna
        calc_def = instance.calculator_definition

        # 3. Wykonaj nowe obliczenia
        try:
            calculator_instance = calculation_logic.CalculatorFactory.get_calculator(calc_def.slug, input_data)
            output_data = decimals_to_float(calculator_instance.calculate())

            with transaction.atomic():
                serializer.save(output_data=output_data)
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages[0] if e.messages else str(e))
        except Exception as e:
            raise DRFValidationError(f"Błąd podczas aktualizacji obliczeń: {e}")

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

        # Admin może pobrać PDF dowolnego obliczenia
        if request.user.is_staff:
            result = get_object_or_404(CalculatorResult, pk=pk)
        else:
            result = self.get_object()

        if result.is_locked and not request.user.is_staff:
            raise PermissionDenied("Odblokuj wyniki, aby pobrać PDF.")

        logo_obj = None
        signature_obj = None

        if request.user.is_staff:
            # Admin może użyć logo wybranego użytkownika: ?preview_user_id=X lub ?use_owner_logo=true
            preview_user_id = request.query_params.get('preview_user_id')
            use_owner_logo = request.query_params.get('use_owner_logo') == 'true'
            target_user_id = preview_user_id or (result.user_id if use_owner_logo else None)
            if target_user_id:
                from django.contrib.auth import get_user_model
                try:
                    target_user = get_user_model().objects.get(pk=target_user_id)
                    logo_obj = UserLogo.objects.filter(user=target_user, is_default=True).first()
                    signature_obj = UserSignature.objects.filter(user=target_user, is_default=True).first()
                except get_user_model().DoesNotExist:
                    pass
        else:
            logo_id = request.query_params.get('logo_id')
            if logo_id:
                try:
                    logo_obj = UserLogo.objects.get(id=logo_id, user=request.user)
                except UserLogo.DoesNotExist:
                    pass

            signature_id = request.query_params.get('signature_id')
            if signature_id:
                try:
                    signature_obj = UserSignature.objects.get(id=signature_id, user=request.user)
                except UserSignature.DoesNotExist:
                    pass
        
        calculator_name = result.calculator_definition.name
        pdf_bytes = generate_result_pdf(result, calculator_name, logo_obj=logo_obj, signature_obj=signature_obj)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        import re as _re
        nr_fab = result.input_data.get('nr_fabryczny', '')
        if isinstance(nr_fab, dict):
            nr_fab = nr_fab.get('value', '') or ''
        nr_fab = _re.sub(r'[^\w\-]', '_', str(nr_fab).strip()) or str(result.id)
        calc_name_safe = _re.sub(r'[^\w\-]', '_', calculator_name)
        response['Content-Disposition'] = f'attachment; filename="{calc_name_safe}_{nr_fab}.pdf"'
        return response

class GenerateLogbookView(rest_framework.views.APIView):
    """Widok do generowania PDF Dziennika Eksploatacji (Logbook)."""
    # Publiczny dostęp (jak w starej wersji), ale z walidacją email w request
    permission_classes = [] 

    def post(self, request):
        from django.http import HttpResponse
        from .book_generator import generate_logbook_pdf
        
        data = request.data
        # Prosta walidacja (opcjonalnie można dodać serializer)
        required = ['email', 'rodzaj_urzadzenia', 'nr_fabryczny', 'nr_udt', 'rok_budowy', 'rok_dop']
        for field in required:
            if not data.get(field):
                return Response({"detail": f"Pole {field} jest wymagane."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Logowanie pobrania (opcjonalnie, można tu dodać zapis do bazy jak w PHP)
        # ...

        pdf_bytes = generate_logbook_pdf(data)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"dziennik_eksploatacji_{data.get('nr_fabryczny', 'utb')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
