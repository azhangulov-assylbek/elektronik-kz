from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext
from django.views.decorators.http import require_POST

from products.models import Product

from users.types import AuthenticatedHttpRequest

from .forms import ReviewForm


@login_required
@require_POST
def add_review(request: AuthenticatedHttpRequest, slug: str) -> HttpResponse:
    """Сохранить отзыв на товар — только если пользователь его покупал и ещё не оставлял отзыв."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if not product.user_has_purchased(request.user):
        messages.error(request, gettext('Оставить отзыв можно только после покупки товара'))
        return redirect('products:product_detail', slug=slug)
    if product.user_has_reviewed(request.user):
        messages.error(request, gettext('Вы уже оставляли отзыв на этот товар'))
        return redirect('products:product_detail', slug=slug)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        messages.success(request, gettext('Спасибо за отзыв!'))
    else:
        messages.error(request, gettext('Не удалось сохранить отзыв — проверьте оценку'))
    return redirect('products:product_detail', slug=slug)
