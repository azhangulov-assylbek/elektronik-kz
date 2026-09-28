"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import URLPattern, URLResolver, include, path

from .seo import SITEMAPS, robots_txt

urlpatterns: list[URLPattern | URLResolver] = [
    # Вне i18n_patterns: robots.txt и sitemap.xml — одни на сайт, в корне.
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='sitemap'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('api.urls')),
]

urlpatterns += i18n_patterns(
    path('users/', include('users.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('', include('reviews.urls')),
    path('', include('products.urls')),
    path('seller/import/', include('bulk_import.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
