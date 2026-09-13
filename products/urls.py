from django.urls import path

from . import seller_views, views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='home'),
    path('product/<str:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('seller/products/', seller_views.product_list, name='seller_product_list'),
    path('seller/products/add/', seller_views.product_create, name='seller_product_add'),
    path('seller/products/<int:pk>/edit/', seller_views.product_edit, name='seller_product_edit'),
]
