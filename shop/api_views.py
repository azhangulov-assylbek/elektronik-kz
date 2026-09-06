from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView

from .models import Product, Review
from .serializers import ProductSerializer, ReviewSerializer


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

        price_min = self.request.query_params.get('price_min')
        if price_min:
            qs = qs.filter(price__gte=price_min)

        price_max = self.request.query_params.get('price_max')
        if price_max:
            qs = qs.filter(price__lte=price_max)

        ordering = self.request.query_params.get('ordering')
        if ordering in ('price', '-price', 'created_at', '-created_at'):
            qs = qs.order_by(ordering)

        return qs


class ProductReviewListCreateView(ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_product(self):
        return Product.objects.active().get(pk=self.kwargs['pk'])

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['pk']).select_related('user')

    def perform_create(self, serializer):
        product = self.get_product()
        user = self.request.user
        if not product.user_has_purchased(user):
            raise PermissionDenied('Оставить отзыв можно только после покупки товара')
        if product.user_has_reviewed(user):
            raise PermissionDenied('Вы уже оставляли отзыв на этот товар')
        serializer.save(product=product, user=user)
