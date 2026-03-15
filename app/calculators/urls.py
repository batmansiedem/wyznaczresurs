from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CalculatorDefinitionViewSet, UnitViewSet, CalculatorResultViewSet, GenerateLogbookView

router = DefaultRouter()
router.register(r'definitions', CalculatorDefinitionViewSet, basename='calculator-definition')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'results', CalculatorResultViewSet, basename='calculator-result')

urlpatterns = [
    path('', include(router.urls)),
    path('generate-logbook/', GenerateLogbookView.as_view(), name='generate-logbook'),
]
