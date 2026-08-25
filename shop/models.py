from django.db import models
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField('название', max_length=100, unique=True)
    slug = models.SlugField('слаг', max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = 'бренд'
        verbose_name_plural = 'бренды'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField('название', max_length=100)
    slug = models.SlugField('слаг', max_length=100, unique=True, blank=True)
    parent = models.ForeignKey(
        'self', verbose_name='родительская категория',
        null=True, blank=True, related_name='children',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField('название', max_length=255)
    slug = models.SlugField('слаг', max_length=255, unique=True, blank=True)
    sku = models.CharField('артикул', max_length=64, unique=True)
    category = models.ForeignKey(
        Category, verbose_name='категория',
        null=True, blank=True, related_name='products',
        on_delete=models.SET_NULL,
    )
    brand = models.ForeignKey(
        Brand, verbose_name='бренд',
        null=True, blank=True, related_name='products',
        on_delete=models.SET_NULL,
    )
    description = models.TextField('описание', blank=True)
    image = models.ImageField('изображение', upload_to='products/', blank=True)
    price = models.DecimalField('цена', max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField('остаток', default=0)
    is_active = models.BooleanField('активен', default=True)
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлён', auto_now=True)

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
