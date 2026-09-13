from django.db.models import Count, Q
from django.views.generic import DetailView, ListView

from reviews.forms import ReviewForm

from .models import Category, Product


class ProductListView(ListView):
    model = Product
    template_name = 'products/home.html'
    context_object_name = 'products'
    paginate_by = 8

    SORT_OPTIONS = {
        'new': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'popular': '-orders_count',
    }

    def get_queryset(self):
        qs = Product.objects.active().select_related('category', 'brand')
        qs = qs.annotate(orders_count=Count('orderitem'))

        self.category = None
        category_slug = self.request.GET.get('category')
        if category_slug:
            self.category = Category.objects.filter(slug=category_slug).first()
            if self.category:
                qs = qs.filter(category=self.category)

        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

        price_min = self.request.GET.get('price_min')
        if price_min:
            qs = qs.filter(price__gte=price_min)

        price_max = self.request.GET.get('price_max')
        if price_max:
            qs = qs.filter(price__lte=price_max)

        sort = self.request.GET.get('sort', 'new')
        qs = qs.order_by(self.SORT_OPTIONS.get(sort, self.SORT_OPTIONS['new']))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.category
        context['query'] = self.request.GET.get('q', '')
        context['sort'] = self.request.GET.get('sort', 'new')
        context['price_min'] = self.request.GET.get('price_min', '')
        context['price_max'] = self.request.GET.get('price_max', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.active().select_related('category', 'brand')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['reviews'] = product.reviews.select_related('user')
        context['has_purchased'] = product.user_has_purchased(self.request.user)
        context['has_reviewed'] = product.user_has_reviewed(self.request.user)
        context['can_review'] = context['has_purchased'] and not context['has_reviewed']
        if context['can_review']:
            context['review_form'] = ReviewForm()
        return context
