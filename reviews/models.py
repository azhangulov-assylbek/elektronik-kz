from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    product = models.ForeignKey(
        'products.Product', verbose_name=_('товар'), related_name='reviews', on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('пользователь'),
        related_name='reviews', on_delete=models.CASCADE,
    )
    rating = models.PositiveSmallIntegerField(_('оценка'), validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(_('комментарий'), blank=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)

    class Meta:
        verbose_name = _('отзыв')
        verbose_name_plural = _('отзывы')
        ordering = ['-created_at']
        unique_together = [('product', 'user')]

    def __str__(self):
        return f'{self.product} — {self.rating}★ от {self.user}'
