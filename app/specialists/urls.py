from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SpecialistViewSet

router = DefaultRouter()
router.register(r'', SpecialistViewSet, basename='specialist')

urlpatterns = [
    path('', include(router.urls)),
]
