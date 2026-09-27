from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView

from products.models import Product

from .models import Review
from .serializers import ReviewSerializer


class ProductReviewListCreateView(ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_product(self):
        return get_object_or_404(Product.objects.active(), pk=self.kwargs['pk'])

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
