from django.db import models
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    """Оплата заказа (мок): способ и статус; картой — сразу «оплачен»."""

    class Method(models.TextChoices):
        CARD = 'card', _('Картой онлайн')
        CASH = 'cash', _('Наличными при получении')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Ожидает оплаты')
        PAID = 'paid', _('Оплачен')

    order = models.OneToOneField(
        'orders.Order', verbose_name=_('заказ'), related_name='payment', on_delete=models.CASCADE,
    )
    method = models.CharField(_('способ оплаты'), max_length=20, choices=Method.choices)
    status = models.CharField(_('статус оплаты'), max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)
    paid_at = models.DateTimeField(_('оплачен'), null=True, blank=True)

    class Meta:
        verbose_name = _('оплата')
        verbose_name_plural = _('оплаты')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Оплата заказа #{self.order_id} — {self.get_method_display()}'
