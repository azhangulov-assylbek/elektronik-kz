from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import AddressForm, LoginForm, ProfileForm, RegistrationForm
from .models import Address


class EmailOrPhoneLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class AccountLogoutView(LogoutView):
    next_page = reverse_lazy('shop:home')


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='accounts.backends.EmailOrPhoneBackend')
            messages.success(request, 'Регистрация прошла успешно')
            return redirect('accounts:profile')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Адрес добавлен')
            return redirect('accounts:addresses')
    else:
        form = AddressForm()

    return render(request, 'accounts/address_form.html', {'form': form})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Адрес обновлён')
            return redirect('accounts:addresses')
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {'form': form})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Адрес удалён')
        return redirect('accounts:addresses')

    return render(request, 'accounts/address_confirm_delete.html', {'address': address})
