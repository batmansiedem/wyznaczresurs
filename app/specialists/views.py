from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Specialist
from .serializers import SpecialistSerializer

class SpecialistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Specialists to be viewed.
    Provides filtering by 'voivodeship' and searching by name, company, and scope.
    """
    queryset = Specialist.objects.filter(is_active=True)
    serializer_class = SpecialistSerializer
    permission_classes = [IsAuthenticated] # Only logged-in users can see specialists

    # Configuration for filtering and searching
    filterset_fields = ['voivodeship']
    search_fields = ['full_name', 'company_name', 'scope_of_activities']
