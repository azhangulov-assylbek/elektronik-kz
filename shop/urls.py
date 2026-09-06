from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='home'),
    path('product/<str:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/<str:slug>/review/', views.add_review, name='add_review'),
]
