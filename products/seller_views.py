from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext

from .forms import ProductForm
from .models import Product


def seller_required(view_func):
    """Доступ только продавцам/администраторам (Product.can_manage_catalog)."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.can_manage_catalog:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@seller_required
def product_list(request):
    products = Product.objects.select_related('category', 'brand').order_by('-created_at')
    return render(request, 'products/seller/product_list.html', {'products': products})


@seller_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, gettext('Товар добавлен'))
            return redirect('products:seller_product_list')
    else:
        form = ProductForm()

    return render(request, 'products/seller/product_form.html', {'form': form, 'is_new': True})


@seller_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, gettext('Товар обновлён'))
            return redirect('products:seller_product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/seller/product_form.html', {'form': form, 'is_new': False, 'product': product})
