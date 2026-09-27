"""Веб-вьюхи личного кабинета: вход/выход, регистрация, профиль, адреса доставки."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext

from .forms import AddressForm, LoginForm, ProfileForm, RegistrationForm
from .models import Address
from .types import AuthenticatedHttpRequest


class EmailOrPhoneLoginView(LoginView):
    """Вход по email или телефону (одно поле, формат определяется автоматически)."""

    template_name = 'users/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class AccountLogoutView(LogoutView):
    """Выход с переходом на главную."""

    next_page = reverse_lazy('products:home')  # type: ignore[assignment]


def register(request: HttpRequest) -> HttpResponse:
    """Регистрация по email или телефону; после успеха пользователь сразу залогинен."""
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='users.backends.EmailOrPhoneBackend')
            messages.success(request, gettext('Регистрация прошла успешно'))
            return redirect('users:profile')
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request: AuthenticatedHttpRequest) -> HttpResponse:
    """Просмотр и редактирование профиля (имя, email, телефон)."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, gettext('Профиль обновлён'))
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})


@login_required
def address_list(request: AuthenticatedHttpRequest) -> HttpResponse:
    """Список адресов доставки текущего пользователя."""
    addresses = request.user.addresses.all()
    return render(request, 'users/address_list.html', {'addresses': addresses})


@login_required
def address_create(request: AuthenticatedHttpRequest) -> HttpResponse:
    """Добавление адреса доставки текущему пользователю."""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, gettext('Адрес добавлен'))
            return redirect('users:addresses')
    else:
        form = AddressForm()

    return render(request, 'users/address_form.html', {'form': form})


@login_required
def address_edit(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Редактирование своего адреса; чужой адрес — 404."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, gettext('Адрес обновлён'))
            return redirect('users:addresses')
    else:
        form = AddressForm(instance=address)

    return render(request, 'users/address_form.html', {'form': form})


@login_required
def address_delete(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Удаление своего адреса: GET — подтверждение, POST — удаление."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, gettext('Адрес удалён'))
        return redirect('users:addresses')

    return render(request, 'users/address_confirm_delete.html', {'address': address})
