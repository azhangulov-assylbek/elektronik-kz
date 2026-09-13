from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'brand', 'description',
            'image', 'price', 'stock', 'is_active',
        ]


class CatalogImportForm(forms.Form):
    file = forms.FileField(label='Файл каталога (CSV или .xlsx)')
