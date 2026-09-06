from django.contrib.auth import get_user_model
from rest_framework import serializers

from .forms import _looks_like_email, normalize_phone

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_identifier(self, value):
        value = value.strip()
        if _looks_like_email(value):
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError('Пользователь с таким email уже зарегистрирован')
            self.context['email'] = value
            self.context['phone'] = None
        else:
            phone = normalize_phone(value)
            if not phone:
                raise serializers.ValidationError('Укажите корректный email или телефон в формате +77001234567')
            if User.objects.filter(phone=phone).exists():
                raise serializers.ValidationError('Пользователь с таким телефоном уже зарегистрирован')
            self.context['email'] = None
            self.context['phone'] = phone
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=self.context.get('email'),
            phone=self.context.get('phone'),
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
