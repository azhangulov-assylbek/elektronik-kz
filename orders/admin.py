from django.contrib import admin
from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'payment_method', 'revenue', 'created_at')
    list_filter = ('status', 'payment_method')
    list_editable = ('status',)
    search_fields = ('id', 'user__email', 'user__phone', 'full_name', 'phone')
    inlines = [OrderItemInline]
    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            revenue_annotated=Sum(
                ExpressionWrapper(F('items__price') * F('items__quantity'), output_field=DecimalField()),
            ),
        )

    @admin.display(description='Сумма', ordering='revenue_annotated')
    def revenue(self, obj):
        return f'{obj.revenue_annotated or 0} ₸'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            queryset = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        summary = queryset.aggregate(
            total_revenue=Sum(
                ExpressionWrapper(F('items__price') * F('items__quantity'), output_field=DecimalField()),
            ),
        )
        response.context_data['summary'] = {
            'orders_count': queryset.count(),
            'total_revenue': summary['total_revenue'] or 0,
        }
        return response

    @admin.action(description='Отметить как подтверждённые')
    def mark_confirmed(self, request, queryset):
        queryset.update(status=Order.Status.CONFIRMED)

    @admin.action(description='Отметить как отправленные')
    def mark_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)

    @admin.action(description='Отметить как доставленные')
    def mark_delivered(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERED)
