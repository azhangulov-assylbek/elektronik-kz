from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# Колонки файла сопоставляются только с этими полями Product — image и
# is_active не маппятся: картинка грузится отдельным шагом
# (batch_images), is_active всегда False до одобрения администратором
# (см. services.py:create_draft_product).
MAPPABLE_FIELDS = {
    'name': _('Название'),
    'sku': _('Артикул'),
    'category': _('Категория'),
    'brand': _('Бренд'),
    'description': _('Описание'),
    'price': _('Цена'),
    'stock': _('Остаток'),
}
REQUIRED_MAPPED_FIELDS = {'name', 'sku', 'price'}


class ImportBatch(models.Model):
    class Status(models.TextChoices):
        UPLOADED = 'uploaded', _('Файл загружен')
        MAPPED = 'mapped', _('Колонки сопоставлены')
        IMAGES_PENDING = 'images_pending', _('Ожидает картинок')
        PENDING_APPROVAL = 'pending_approval', _('На модерации')
        APPROVED = 'approved', _('Одобрено')
        REJECTED = 'rejected', _('Отклонено')

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('продавец'),
        related_name='import_batches', on_delete=models.CASCADE,
    )
    file = models.FileField(_('файл'), upload_to='imports/%Y/%m/')
    status = models.CharField(_('статус'), max_length=20, choices=Status.choices, default=Status.UPLOADED)
    column_mapping = models.JSONField(_('сопоставление колонок'), blank=True, default=dict)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлён'), auto_now=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('проверил'),
        null=True, blank=True, related_name='reviewed_import_batches', on_delete=models.SET_NULL,
    )
    reviewed_at = models.DateTimeField(_('когда проверено'), null=True, blank=True)
    rejection_reason = models.CharField(_('причина отклонения'), max_length=255, blank=True)

    class Meta:
        verbose_name = _('импорт каталога')
        verbose_name_plural = _('импорты каталога')
        ordering = ['-created_at']

    def __str__(self):
        return f'Импорт #{self.pk} ({self.get_status_display()})'

    @property
    def all_images_uploaded(self):
        rows = self.rows.filter(product__isnull=False)
        return rows.exists() and not rows.filter(product__image='').exists()


class ImportRow(models.Model):
    batch = models.ForeignKey(ImportBatch, verbose_name=_('импорт'), related_name='rows', on_delete=models.CASCADE)
    row_number = models.PositiveIntegerField(_('номер строки'))
    raw_data = models.JSONField(_('данные строки'), default=dict)
    product = models.ForeignKey(
        'products.Product', verbose_name=_('товар'),
        null=True, blank=True, related_name='import_rows', on_delete=models.SET_NULL,
    )
    error = models.CharField(_('ошибка'), max_length=255, blank=True)

    class Meta:
        verbose_name = _('строка импорта')
        verbose_name_plural = _('строки импорта')
        ordering = ['row_number']

    def __str__(self):
        return f'Строка {self.row_number} импорта #{self.batch_id}'
