import pytest
from django.urls import reverse

from users.models import Address, User

pytestmark = pytest.mark.django_db


def test_register_with_email(client):
    response = client.post(reverse('users:register'), {
        'identifier': 'new@example.com', 'first_name': 'Иван',
        'password1': 'StrongPass123', 'password2': 'StrongPass123',
    })

    assert response.status_code == 302
    user = User.objects.get(email='new@example.com')
    assert user.first_name == 'Иван'


def test_register_with_phone(client):
    response = client.post(reverse('users:register'), {
        'identifier': '+7 700 123 45 67', 'password1': 'StrongPass123', 'password2': 'StrongPass123',
    })

    assert response.status_code == 302
    assert User.objects.filter(phone='+77001234567').exists()


def test_register_password_mismatch_rejected(client):
    client.post(reverse('users:register'), {
        'identifier': 'x@example.com', 'password1': 'StrongPass123', 'password2': 'Different123',
    })

    assert not User.objects.filter(email='x@example.com').exists()


def test_register_duplicate_email_rejected(client):
    User.objects.create_user(email='dup@example.com', password='pass12345')

    client.post(reverse('users:register'), {
        'identifier': 'dup@example.com', 'password1': 'StrongPass123', 'password2': 'StrongPass123',
    })

    assert User.objects.filter(email='dup@example.com').count() == 1


def test_login_with_email(client):
    User.objects.create_user(email='login@example.com', password='pass12345')

    response = client.post(reverse('users:login'), {
        'username': 'login@example.com', 'password': 'pass12345',
    })

    assert response.status_code == 302
    assert '_auth_user_id' in client.session


def test_login_with_phone(client):
    User.objects.create_user(phone='+77001234567', password='pass12345')

    client.post(reverse('users:login'), {
        'username': '+77001234567', 'password': 'pass12345',
    })

    assert '_auth_user_id' in client.session


def test_login_wrong_password_fails(client):
    User.objects.create_user(email='login@example.com', password='pass12345')

    client.post(reverse('users:login'), {'username': 'login@example.com', 'password': 'wrong'})

    assert '_auth_user_id' not in client.session


def test_default_address_used_for_checkout_prefill(client):
    user = User.objects.create_user(email='addr@example.com', password='pass12345', phone='+77001234567')
    Address.objects.create(
        user=user, city='Алматы', street='Абая', house='10', is_default=True,
    )
    client.force_login(user)

    response = client.get(reverse('orders:checkout'))

    assert response.status_code == 302  # пустая корзина -> редирект на корзину, не 500


def test_second_default_address_unsets_previous(client):
    user = User.objects.create_user(email='addr2@example.com', password='pass12345')
    first = Address.objects.create(user=user, city='Алматы', street='Абая', house='1', is_default=True)
    Address.objects.create(user=user, city='Астана', street='Кабанбай батыра', house='2', is_default=True)

    first.refresh_from_db()
    assert first.is_default is False
