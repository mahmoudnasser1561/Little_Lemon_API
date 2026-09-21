from rest_framework import serializers
from rest_framework.serializers import as_serializer_error
from django.core.exceptions import ValidationError
from .models import DeliveryCrewUser

class DeliveryCrewUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCrewUser
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        try:
            return DeliveryCrewUser.objects.create_user(**validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(as_serializer_error(e))
