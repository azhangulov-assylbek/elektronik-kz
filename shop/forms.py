from django import forms

from .models import Product, Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} ★') for i in range(1, 6)]),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'brand', 'description',
            'image', 'price', 'stock', 'is_active',
        ]


class CatalogImportForm(forms.Form):
    file = forms.FileField(label='Файл каталога (CSV или .xlsx)')
