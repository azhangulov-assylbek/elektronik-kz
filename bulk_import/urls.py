from django.urls import path

from . import views

app_name = 'bulk_import'

urlpatterns = [
    path('', views.batch_list, name='batch_list'),
    path('upload/', views.batch_upload, name='batch_upload'),
    path('<int:pk>/map/', views.batch_map, name='batch_map'),
    path('<int:pk>/preview/', views.batch_preview, name='batch_preview'),
    path('<int:pk>/images/', views.batch_images, name='batch_images'),
    path('<int:pk>/images/<int:row_id>/upload/', views.batch_image_upload, name='batch_image_upload'),
    path('<int:pk>/submit/', views.batch_submit, name='batch_submit'),
    path('moderation/', views.moderation_list, name='moderation_list'),
    path('moderation/<int:pk>/', views.moderation_detail, name='moderation_detail'),
]
