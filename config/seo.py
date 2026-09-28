"""robots.txt и sitemap.xml для поисковиков (Google, Яндекс)."""
from datetime import datetime

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET

from products.models import Product


class _I18nSitemap(Sitemap):
    """Каждая страница — в русской (без префикса) и казахской (/kk/) версии, с hreflang-ссылками между ними."""

    i18n = True
    alternates = True
    x_default = True


class StaticViewSitemap(_I18nSitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self) -> list[str]:
        return ['products:home']

    def location(self, item: str) -> str:
        return reverse(item)


class ProductSitemap(_I18nSitemap):
    """Только активные товары: неактивные и ожидающие модерации импорта в поиск не попадают."""

    priority = 0.8
    changefreq = 'weekly'

    def items(self) -> QuerySet[Product]:
        return Product.objects.active().order_by('pk')

    def location(self, item: Product) -> str:
        return reverse('products:product_detail', args=[item.slug])

    def lastmod(self, item: Product) -> datetime:
        return item.updated_at


SITEMAPS = {'static': StaticViewSitemap, 'products': ProductSitemap}

# Служебные разделы — индексировать нечего (формы, личные данные, корзина).
_PRIVATE_PREFIXES = ['users/', 'cart/', 'orders/', 'seller/']
# Дубли каталога: поиск, сортировка и фильтр цены дают те же товары в другом
# порядке/подмножестве. Пагинация (?page=) и категории (?category=) разрешены.
_DUPLICATE_PARAMS = ['q', 'sort', 'min_price', 'max_price']


@require_GET
def robots_txt(request: HttpRequest) -> HttpResponse:
    """robots.txt: закрыть служебные разделы на всех языках и дубли каталога, указать sitemap."""
    lines = ['User-agent: *', 'Disallow: /admin/', 'Disallow: /api/', 'Disallow: /i18n/']
    language_prefixes = [''] + [
        f'{code}/' for code, _name in settings.LANGUAGES if code != settings.LANGUAGE_CODE
    ]
    for language_prefix in language_prefixes:
        lines += [f'Disallow: /{language_prefix}{path}' for path in _PRIVATE_PREFIXES]
    lines += [f'Disallow: /*?*{param}=' for param in _DUPLICATE_PARAMS]
    lines += ['', f'Sitemap: {request.build_absolute_uri(reverse("sitemap"))}']
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain; charset=utf-8')
