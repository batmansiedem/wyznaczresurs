from rest_framework import serializers

class ContactFormSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True, max_length=100)
    subject = serializers.CharField(required=False, allow_blank=True, max_length=255)
    message = serializers.CharField()
