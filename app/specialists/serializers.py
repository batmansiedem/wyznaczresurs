from rest_framework import serializers
from .models import Specialist

class SpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = ['id', 'full_name', 'company_name', 'scope_of_activities', 'contact_details', 'voivodeship', 'is_active']
