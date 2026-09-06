from django.contrib import admin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum

from .models import Brand, Category, Product, Review


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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__email', 'user__phone')
