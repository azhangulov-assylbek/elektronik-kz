from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import redirect, render
from django.urls import path

from .catalog_import import import_catalog
from .forms import CatalogImportForm
from .models import Brand, Category, Product


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    list_filter = ('parent',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'brand', 'price', 'stock', 'is_active', 'total_sold', 'revenue')
    list_filter = ('category', 'brand', 'is_active')
    list_editable = ('price', 'stock', 'is_active')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            total_sold_annotated=Sum('orderitem__quantity'),
            revenue_annotated=Sum(
                ExpressionWrapper(F('orderitem__price') * F('orderitem__quantity'), output_field=DecimalField()),
            ),
        )

    @admin.display(description='Продано, шт.', ordering='total_sold_annotated')
    def total_sold(self, obj):
        return obj.total_sold_annotated or 0

    @admin.display(description='Выручка', ordering='revenue_annotated')
    def revenue(self, obj):
        return f'{obj.revenue_annotated or 0} ₸'

    def get_urls(self):
        custom_urls = [
            path('import-catalog/', self.admin_site.admin_view(self.import_catalog_view),
                 name='products_product_import_catalog'),
        ]
        return custom_urls + super().get_urls()

    def import_catalog_view(self, request):
        if not request.user.can_bulk_import_catalog:
            raise PermissionDenied

        if request.method == 'POST':
            form = CatalogImportForm(request.POST, request.FILES)
            if form.is_valid():
                result = import_catalog(request.FILES['file'])
                for error in result.errors[:20]:
                    messages.error(request, error)
                if result.created or result.updated:
                    messages.success(
                        request,
                        f'Импорт завершён: создано {result.created}, обновлено {result.updated}',
                    )
                return redirect('admin:products_product_changelist')
        else:
            form = CatalogImportForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Импорт каталога товаров',
            'opts': self.model._meta,
        }
        return render(request, 'admin/products/product/import_catalog.html', context)
