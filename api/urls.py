from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from cart.api_views import CartView
from orders.api_views import OrderViewSet
from products.api_views import ProductViewSet
from reviews.api_views import ProductReviewListCreateView
from users.api_views import LoginView, RegisterView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    path('users/register/', RegisterView.as_view(), name='api-register'),
    path('users/login/', LoginView.as_view(), name='api-login'),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('cart/', CartView.as_view(), name='api-cart'),
    path('products/<int:pk>/reviews/', ProductReviewListCreateView.as_view(), name='api-product-reviews'),
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('', include(router.urls)),
]
