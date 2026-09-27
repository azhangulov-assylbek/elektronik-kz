from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    """Заказ пользователя с данными доставки; оплата — в payments.Payment (OneToOne)."""

    class Status(models.TextChoices):
        NEW = 'new', _('Новый')
        PAID = 'paid', _('Оплачен')
        CONFIRMED = 'confirmed', _('Подтверждён')
        SHIPPED = 'shipped', _('Отправлен')
        DELIVERED = 'delivered', _('Доставлен')
        CANCELLED = 'cancelled', _('Отменён')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('пользователь'),
        related_name='orders', on_delete=models.CASCADE,
    )
    status = models.CharField(_('статус'), max_length=20, choices=Status.choices, default=Status.NEW)
    full_name = models.CharField(_('получатель'), max_length=200)
    phone = models.CharField(_('телефон'), max_length=20)
    city = models.CharField(_('город'), max_length=100)
    street = models.CharField(_('улица'), max_length=255)
    house = models.CharField(_('дом'), max_length=20)
    apartment = models.CharField(_('квартира/офис'), max_length=20, blank=True)
    comment = models.CharField(_('комментарий'), max_length=255, blank=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)

    class Meta:
        verbose_name = _('заказ')
        verbose_name_plural = _('заказы')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Заказ #{self.pk}'

    @property
    def total_price(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), start=Decimal(0))


class OrderItem(models.Model):
    """Позиция заказа: цена и название — снимок на момент оформления, а не ссылка на текущие."""

    order = models.ForeignKey(Order, verbose_name=_('заказ'), related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', verbose_name=_('товар'), on_delete=models.PROTECT)
    product_name = models.CharField(_('название товара'), max_length=255)
    price = models.DecimalField(_('цена'), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_('количество'), default=1)

    class Meta:
        verbose_name = _('позиция заказа')
        verbose_name_plural = _('позиции заказа')

    def __str__(self) -> str:
        return f'{self.product_name} x{self.quantity}'

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity
