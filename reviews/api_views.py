"""REST API отзывов: /api/products/<id>/reviews/ — список (всем) и добавление (после покупки)."""
from typing import cast

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView

from products.models import Product

from users.models import User

from .models import Review
from .serializers import ReviewSerializer


class ProductReviewListCreateView(ListCreateAPIView):
    """Отзывы на товар. Оставить отзыв можно один раз и только после покупки."""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_product(self) -> Product:
        return get_object_or_404(Product.objects.active(), pk=self.kwargs['pk'])

    def get_queryset(self) -> QuerySet[Review]:
        return Review.objects.filter(product_id=self.kwargs['pk']).select_related('user')

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        product = self.get_product()
        user = cast(User, self.request.user)  # POST закрыт IsAuthenticatedOrReadOnly
        if not product.user_has_purchased(user):
            raise PermissionDenied('Оставить отзыв можно только после покупки товара')
        if product.user_has_reviewed(user):
            raise PermissionDenied('Вы уже оставляли отзыв на этот товар')
        serializer.save(product=product, user=user)
