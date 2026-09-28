from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .forms import _looks_like_email, normalize_phone

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Регистрация через API: identifier — email или телефон, как в веб-форме."""

    identifier = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_identifier(self, value: str) -> str:
        """Проверить identifier и вернуть его нормализованным: email как есть, телефон — в виде +7XXXXXXXXXX."""
        value = value.strip()
        if _looks_like_email(value):
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError('Пользователь с таким email уже зарегистрирован')
            return value

        phone = normalize_phone(value)
        if not phone:
            raise serializers.ValidationError('Укажите корректный email или телефон в формате +77001234567')
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError('Пользователь с таким телефоном уже зарегистрирован')
        return phone

    def create(self, validated_data: dict[str, Any]) -> Any:
        identifier = validated_data['identifier']
        is_email = _looks_like_email(identifier)
        return User.objects.create_user(
            email=identifier if is_email else None,
            phone=None if is_email else identifier,
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
        )


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name']
