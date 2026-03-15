from rest_framework import serializers

class SendEmailSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Lista ID użytkowników do których wysłać email. Jeśli puste, wysyła do wszystkich."
    )
    subject = serializers.CharField(max_length=255)
    content = serializers.CharField()
    all_users = serializers.BooleanField(default=False)
    include_bonus_code = serializers.BooleanField(default=False)
    bonus_points = serializers.IntegerField(required=False, min_value=1)
