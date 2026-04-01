from rest_framework import serializers

class ContactFormSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=100)
    subject = serializers.CharField(required=False, allow_blank=True, max_length=255)
    message = serializers.CharField()

    def validate(self, attrs):
        # Jeśli użytkownik nie jest zalogowany (brak request.user w context), name i email są wymagane
        request = self.context.get('request')
        if request and not request.user.is_authenticated:
            if not attrs.get('name'):
                raise serializers.ValidationError({"name": "To pole jest wymagane dla gości."})
            if not attrs.get('email'):
                raise serializers.ValidationError({"email": "To pole jest wymagane dla gości."})
        return attrs
