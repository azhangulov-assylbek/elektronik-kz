from django.db.models import Q
from rest_framework import permissions, viewsets

from .models import Product
from .serializers import ProductSerializer
from .utils import parse_price


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.active().select_related('category', 'brand')

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)

        query = self.request.query_params.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

        price_min = parse_price(self.request.query_params.get('price_min'))
        if price_min is not None:
            qs = qs.filter(price__gte=price_min)

        price_max = parse_price(self.request.query_params.get('price_max'))
        if price_max is not None:
            qs = qs.filter(price__lte=price_max)

        ordering = self.request.query_params.get('ordering')
        if ordering in ('price', '-price', 'created_at', '-created_at'):
            qs = qs.order_by(ordering)

        return qs
