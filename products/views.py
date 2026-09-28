"""Веб-вьюхи каталога: список товаров с фильтрами и страница товара."""
from typing import Any

from django.db.models import Avg, Count, Q, QuerySet
from django.views.generic import DetailView, ListView

from reviews.forms import ReviewForm

from .models import Category, Product
from .utils import parse_price


class ProductListView(ListView):
    """Каталог (главная): поиск ?q=, категории ?category= (можно несколько), цена ?min_price=/?max_price=,
    сортировка ?sort=new|price_asc|price_desc|popular|rating, пагинация по 9."""

    model = Product
    template_name = 'products/home.html'
    context_object_name = 'products'
    paginate_by = 9

    def get_queryset(self) -> QuerySet[Product]:
        qs = (
            Product.objects.active()
            .select_related('category', 'brand')
            .annotate(avg_rating=Avg('reviews__rating'), orders_count=Count('orderitem'))
        )

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

        categories = self.request.GET.getlist('category')
        if categories:
            qs = qs.filter(category__slug__in=categories)

        min_price = parse_price(self.request.GET.get('min_price'))
        max_price = parse_price(self.request.GET.get('max_price'))

        if min_price is not None:
            qs = qs.filter(price__gte=min_price)

        if max_price is not None:
            qs = qs.filter(price__lte=max_price)

        sort_map = {
            'new': '-created_at',
            'price_asc': 'price',
            'price_desc': '-price',
            'popular': '-orders_count',
            'rating': '-avg_rating',
        }
        sort = self.request.GET.get('sort', 'new')
        return qs.order_by(sort_map.get(sort, '-created_at'))

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['query'] = self.request.GET.get('q', '')
        ctx['min_price'] = self.request.GET.get('min_price', '')
        ctx['max_price'] = self.request.GET.get('max_price', '')
        ctx['selected_categories'] = self.request.GET.getlist('category')
        ctx['current_sort'] = self.request.GET.get('sort', 'new')

        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['querystring'] = params.urlencode()
        return ctx


class ProductDetailView(DetailView):
    """Страница товара: детали, средний рейтинг, отзывы и форма отзыва (если товар куплен и отзыва ещё нет)."""

    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self) -> QuerySet[Product]:
        return (
            Product.objects.active()
            .select_related('category', 'brand')
            .annotate(avg_rating=Avg('reviews__rating'))
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        product = self.object
        ctx['reviews'] = product.reviews.select_related('user')
        ctx['has_purchased'] = product.user_has_purchased(self.request.user)
        ctx['has_reviewed'] = product.user_has_reviewed(self.request.user)
        ctx['can_review'] = ctx['has_purchased'] and not ctx['has_reviewed']
        ctx['review_form'] = ReviewForm() if ctx['can_review'] else None
        return ctx
