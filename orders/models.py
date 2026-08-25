from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        CONFIRMED = 'confirmed', 'Подтверждён'
        SHIPPED = 'shipped', 'Отправлен'
        DELIVERED = 'delivered', 'Доставлен'
        CANCELLED = 'cancelled', 'Отменён'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='пользователь',
        related_name='orders', on_delete=models.CASCADE,
    )
    status = models.CharField('статус', max_length=20, choices=Status.choices, default=Status.NEW)
    full_name = models.CharField('получатель', max_length=200)
    phone = models.CharField('телефон', max_length=20)
    city = models.CharField('город', max_length=100)
    street = models.CharField('улица', max_length=255)
    house = models.CharField('дом', max_length=20)
    apartment = models.CharField('квартира/офис', max_length=20, blank=True)
    comment = models.CharField('комментарий', max_length=255, blank=True)
    created_at = models.DateTimeField('создан', auto_now_add=True)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk}'

    @property
    def total_price(self):
        return sum((item.subtotal for item in self.items.all()), start=0)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='заказ', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('shop.Product', verbose_name='товар', on_delete=models.PROTECT)
    product_name = models.CharField('название товара', max_length=255)
    price = models.DecimalField('цена', max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField('количество', default=1)

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity
