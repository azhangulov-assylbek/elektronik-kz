"""Пошаговый импорт каталога продавцом и модерация импортов администратором.

Шаги продавца: загрузка файла → сопоставление колонок → превью → создание
черновых товаров (is_active=False) → картинки → отправка на модерацию.
"""
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext

from products.models import Product
from products.seller_views import seller_required
from users.types import AuthenticatedHttpRequest

from .forms import BatchUploadForm, ColumnMappingForm, RejectBatchForm, RowImageForm
from .models import MAPPABLE_FIELDS, ImportBatch
from .services import build_rows_from_mapping, create_draft_products_for_batch, parse_file

PREVIEW_ROWS = 5
ROWS_PAGE_SIZE = 20


def moderator_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Доступ только администраторам (User.can_bulk_import_catalog)."""
    @wraps(view_func)
    @login_required
    def wrapper(request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.can_bulk_import_catalog:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@seller_required
def batch_list(request: AuthenticatedHttpRequest) -> HttpResponse:
    """Свои импорты продавца со статусами."""
    batches = request.user.import_batches.all()
    return render(request, 'bulk_import/batch_list.html', {'batches': batches})


@seller_required
def batch_upload(request: AuthenticatedHttpRequest) -> HttpResponse:
    """Шаг 1: загрузка файла CSV/.xlsx."""
    if request.method == 'POST':
        form = BatchUploadForm(request.POST, request.FILES)
        if form.is_valid():
            batch = ImportBatch.objects.create(seller=request.user, file=form.cleaned_data['file'])
            return redirect('bulk_import:batch_map', pk=batch.pk)
    else:
        form = BatchUploadForm()

    return render(request, 'bulk_import/batch_upload.html', {'form': form})


@seller_required
def batch_map(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Шаг 2: превью первых строк и сопоставление колонок файла полям товара."""
    batch = get_object_or_404(ImportBatch, pk=pk, seller=request.user)
    headers, rows = parse_file(batch.file)
    preview_rows = rows[:PREVIEW_ROWS]

    if request.method == 'POST':
        form = ColumnMappingForm(request.POST, headers=headers)
        if form.is_valid():
            batch.column_mapping = form.get_mapping()
            batch.status = ImportBatch.Status.MAPPED
            batch.save(update_fields=['column_mapping', 'status'])
            build_rows_from_mapping(batch)
            return redirect('bulk_import:batch_preview', pk=batch.pk)
    else:
        form = ColumnMappingForm(headers=headers)

    return render(request, 'bulk_import/batch_map.html', {
        'batch': batch, 'form': form, 'columns': list(zip(headers, form)),
        'headers': headers, 'preview_rows': preview_rows,
    })


@seller_required
def batch_preview(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Шаг 3: данные по маппингу; POST создаёт черновые товары (is_active=False)."""
    batch = get_object_or_404(ImportBatch, pk=pk, seller=request.user)
    field_names = list(dict.fromkeys(batch.column_mapping.values()))

    if request.method == 'POST':
        create_draft_products_for_batch(batch)
        batch.status = ImportBatch.Status.IMAGES_PENDING
        batch.save(update_fields=['status'])
        messages.success(request, gettext('Товары созданы черновиком. Теперь загрузите картинки к каждому.'))
        return redirect('bulk_import:batch_images', pk=batch.pk)

    page_obj = Paginator(batch.rows.all(), ROWS_PAGE_SIZE).get_page(request.GET.get('page'))
    field_labels = [MAPPABLE_FIELDS.get(name, name) for name in field_names]
    rows_with_values = [(row, [row.raw_data.get(name, '') for name in field_names]) for row in page_obj]
    return render(request, 'bulk_import/batch_preview.html', {
        'batch': batch, 'field_labels': field_labels, 'rows_with_values': rows_with_values, 'page_obj': page_obj,
    })


@seller_required
def batch_images(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Шаг 4: список созданных товаров для загрузки картинок."""
    batch = get_object_or_404(ImportBatch, pk=pk, seller=request.user)
    rows_qs = batch.rows.filter(product__isnull=False).select_related('product')
    page_obj = Paginator(rows_qs, ROWS_PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'bulk_import/batch_images.html', {'batch': batch, 'rows': page_obj, 'page_obj': page_obj})


@seller_required
def batch_image_upload(request: AuthenticatedHttpRequest, pk: int, row_id: int) -> HttpResponse:
    """Загрузить картинку к одному товару импорта."""
    batch = get_object_or_404(ImportBatch, pk=pk, seller=request.user)
    row = get_object_or_404(batch.rows.select_related('product'), pk=row_id, product__isnull=False)

    if request.method == 'POST':
        form = RowImageForm(request.POST, request.FILES)
        if form.is_valid():
            product = row.product
            assert product is not None  # отфильтровано product__isnull=False выше
            product.image = form.cleaned_data['image']
            product.save(update_fields=['image'])
            messages.success(request, gettext('Картинка сохранена: %(name)s') % {'name': product.name})
        else:
            messages.error(request, gettext('Не удалось загрузить картинку — проверьте формат файла'))

    return redirect('bulk_import:batch_images', pk=batch.pk)


@seller_required
def batch_submit(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Шаг 5: отправить на модерацию — только когда у всех товаров есть картинка."""
    batch = get_object_or_404(ImportBatch, pk=pk, seller=request.user)

    if request.method == 'POST':
        if not batch.all_images_uploaded:
            messages.error(request, gettext('Сначала загрузите картинки ко всем товарам.'))
            return redirect('bulk_import:batch_images', pk=batch.pk)

        batch.status = ImportBatch.Status.PENDING_APPROVAL
        batch.save(update_fields=['status'])
        messages.success(request, gettext('Импорт отправлен на подтверждение администратору.'))

    return redirect('bulk_import:batch_list')


@moderator_required
def moderation_list(request: AuthenticatedHttpRequest) -> HttpResponse:
    """Импорты, ожидающие решения администратора."""
    batches = ImportBatch.objects.filter(status=ImportBatch.Status.PENDING_APPROVAL).select_related('seller')
    return render(request, 'bulk_import/moderation_list.html', {'batches': batches})


@moderator_required
def moderation_detail(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Товары импорта; POST action=approve публикует их в каталоге, action=reject — отклоняет с причиной."""
    batch = get_object_or_404(ImportBatch, pk=pk, status=ImportBatch.Status.PENDING_APPROVAL)
    rows = batch.rows.filter(product__isnull=False).select_related('product')
    form = RejectBatchForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            product_ids = rows.values_list('product_id', flat=True)
            Product.objects.filter(pk__in=product_ids).update(is_active=True)
            batch.status = ImportBatch.Status.APPROVED
            batch.reviewed_by = request.user
            batch.reviewed_at = timezone.now()
            batch.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
            messages.success(request, gettext('Импорт одобрен, товары опубликованы в каталоге.'))
            return redirect('bulk_import:moderation_list')
        if action == 'reject':
            form = RejectBatchForm(request.POST)
            if form.is_valid():
                batch.status = ImportBatch.Status.REJECTED
                batch.reviewed_by = request.user
                batch.reviewed_at = timezone.now()
                batch.rejection_reason = form.cleaned_data['rejection_reason']
                batch.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])
                messages.success(request, gettext('Импорт отклонён.'))
                return redirect('bulk_import:moderation_list')

    return render(request, 'bulk_import/moderation_detail.html', {'batch': batch, 'rows': rows, 'form': form})
