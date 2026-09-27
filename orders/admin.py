from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Заказы в админке: сумма по каждому заказу, итоги по выборке и массовая смена статуса."""

    list_display = ('id', 'user', 'status', 'payment_method', 'revenue', 'created_at')
    list_filter = ('status', 'payment__method')
    list_editable = ('status',)
    search_fields = ('id', 'user__email', 'user__phone', 'full_name', 'phone')
    inlines = [OrderItemInline]
    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered']

    @admin.display(description='Способ оплаты')
    def payment_method(self, obj: Order) -> str:
        payment = getattr(obj, 'payment', None)
        return payment.get_method_display() if payment else '—'

    def get_queryset(self, request: HttpRequest) -> QuerySet[Order]:
        return super().get_queryset(request).annotate(
            revenue_annotated=Sum(
                ExpressionWrapper(F('items__price') * F('items__quantity'), output_field=DecimalField()),
            ),
        )

    @admin.display(description='Сумма', ordering='revenue_annotated')
    def revenue(self, obj: Order) -> str:
        # revenue_annotated добавляется в get_queryset, у самой модели такого поля нет.
        return f'{getattr(obj, "revenue_annotated", None) or 0} ₸'

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, object] | None = None) -> HttpResponse:
        """Добавить над списком заказов итог по текущей выборке (с учётом фильтров): количество и выручку."""
        response = super().changelist_view(request, extra_context)
        if not isinstance(response, TemplateResponse) or response.context_data is None:
            return response
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
    def mark_confirmed(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        queryset.update(status=Order.Status.CONFIRMED)

    @admin.action(description='Отметить как отправленные')
    def mark_shipped(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        queryset.update(status=Order.Status.SHIPPED)

    @admin.action(description='Отметить как доставленные')
    def mark_delivered(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        queryset.update(status=Order.Status.DELIVERED)
