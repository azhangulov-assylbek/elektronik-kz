from django.shortcuts import render

from .models import Product


def home(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    return render(request, 'shop/home.html', {'products': products})
