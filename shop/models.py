from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def make_unique_slug(model_cls, name, slug_field='slug'):
    """slugify с allow_unicode (иначе кириллические названия дают пустой
    слаг) и защитой от коллизий при одинаковых названиях."""
    base = slugify(name, allow_unicode=True) or 'item'
    slug = base
    n = 1
    while model_cls.objects.filter(**{slug_field: slug}).exists():
        n += 1
        slug = f'{base}-{n}'
    return slug


class Brand(models.Model):
    name = models.CharField(_('название'), max_length=100, unique=True)
    slug = models.SlugField(_('слаг'), max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = _('бренд')
        verbose_name_plural = _('бренды')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(type(self), self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(_('название'), max_length=100)
    slug = models.SlugField(_('слаг'), max_length=100, unique=True, blank=True)
    parent = models.ForeignKey(
        'self', verbose_name=_('родительская категория'),
        null=True, blank=True, related_name='children',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('категория')
        verbose_name_plural = _('категории')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(type(self), self.name)
        super().save(*args, **kwargs)


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Product(models.Model):
    name = models.CharField(_('название'), max_length=255)
    slug = models.SlugField(_('слаг'), max_length=255, unique=True, blank=True)
    sku = models.CharField(_('артикул'), max_length=64, unique=True)
    category = models.ForeignKey(
        Category, verbose_name=_('категория'),
        null=True, blank=True, related_name='products',
        on_delete=models.SET_NULL,
    )
    brand = models.ForeignKey(
        Brand, verbose_name=_('бренд'),
        null=True, blank=True, related_name='products',
        on_delete=models.SET_NULL,
    )
    description = models.TextField(_('описание'), blank=True)
    image = models.ImageField(_('изображение'), upload_to='products/', blank=True)
    price = models.DecimalField(_('цена'), max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(_('остаток'), default=0)
    is_active = models.BooleanField(_('активен'), default=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлён'), auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = _('товар')
        verbose_name_plural = _('товары')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(type(self), self.name)
        super().save(*args, **kwargs)

    def user_has_purchased(self, user):
        if not user.is_authenticated:
            return False
        return self.orderitem_set.filter(order__user=user).exists()

    def user_has_reviewed(self, user):
        if not user.is_authenticated:
            return False
        return self.reviews.filter(user=user).exists()


class Review(models.Model):
    product = models.ForeignKey(Product, verbose_name=_('товар'), related_name='reviews', on_delete=models.CASCADE)
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
