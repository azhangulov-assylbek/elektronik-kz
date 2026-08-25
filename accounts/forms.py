import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Address

User = get_user_model()


def _looks_like_email(value):
    return '@' in value


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email или телефон')

    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if not _looks_like_email(value):
            value = normalize_phone(value) or value
        return value


def normalize_phone(raw):
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits[0] in ('7', '8'):
        return '+7' + digits[1:]
    if len(digits) == 10:
        return '+7' + digits
    return None


class RegistrationForm(forms.Form):
    identifier = forms.CharField(
        label='Email или телефон',
        help_text='Например, ivan@example.com или +77001234567',
    )
    first_name = forms.CharField(label='Имя', max_length=100, required=False)
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        identifier = cleaned.get('identifier', '').strip()
        if identifier:
            if _looks_like_email(identifier):
                cleaned['email'] = identifier
                cleaned['phone'] = None
                if User.objects.filter(email__iexact=identifier).exists():
                    self.add_error('identifier', 'Пользователь с таким email уже зарегистрирован')
            else:
                phone = normalize_phone(identifier)
                if not phone:
                    self.add_error('identifier', 'Укажите корректный email или телефон в формате +77001234567')
                else:
                    cleaned['email'] = None
                    cleaned['phone'] = phone
                    if User.objects.filter(phone=phone).exists():
                        self.add_error('identifier', 'Пользователь с таким телефоном уже зарегистрирован')

        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Пароли не совпадают')
        return cleaned

    def save(self):
        return User.objects.create_user(
            email=self.cleaned_data.get('email'),
            phone=self.cleaned_data.get('phone'),
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data.get('first_name', ''),
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Этот email уже используется')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Этот телефон уже используется')
        return phone

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('email') and not cleaned.get('phone'):
            raise ValidationError('Укажите хотя бы email или телефон')
        return cleaned


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['city', 'street', 'house', 'apartment', 'postal_code', 'comment', 'is_default']
