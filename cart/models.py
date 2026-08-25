from django.conf import settings
from django.db import models


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name='пользователь',
        null=True, blank=True, related_name='cart', on_delete=models.CASCADE,
    )
    session_key = models.CharField('ключ сессии', max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField('создана', auto_now_add=True)
    updated_at = models.DateTimeField('обновлена', auto_now=True)

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'корзины'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name='cart_has_user_or_session',
            ),
        ]

    def __str__(self):
        return f'Корзина {self.user or self.session_key}'

    @property
    def total_price(self):
        return sum((item.subtotal for item in self.items.all()), start=0)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def merge_from(self, other_cart):
        for item in other_cart.items.select_related('product'):
            own_item, created = self.items.get_or_create(
                product=item.product,
                defaults={'quantity': item.quantity},
            )
            if not created:
                own_item.quantity += item.quantity
                own_item.save(update_fields=['quantity'])
        other_cart.delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, verbose_name='корзина', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('shop.Product', verbose_name='товар', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField('количество', default=1)
    added_at = models.DateTimeField('добавлен', auto_now_add=True)

    class Meta:
        verbose_name = 'товар в корзине'
        verbose_name_plural = 'товары в корзине'
        unique_together = [('cart', 'product')]

    def __str__(self):
        return f'{self.product} x{self.quantity}'

    @property
    def subtotal(self):
        return self.product.price * self.quantity
