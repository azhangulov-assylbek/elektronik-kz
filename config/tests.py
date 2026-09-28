import pytest

from products.models import Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def products():
    return {
        'active': Product.objects.create(name='Acer Nitro 5', sku='SEO-1', price=459990, stock=3),
        # Латиница — чтобы slug в sitemap не был percent-encoded и проверка «нет в sitemap» была осмысленной.
        'hidden': Product.objects.create(name='Hidden Draft', sku='SEO-2', price=1000, stock=1, is_active=False),
    }


def test_robots_txt_closes_private_sections_and_points_to_sitemap(client):
    response = client.get('/robots.txt')

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/plain')
    body = response.content.decode()
    for path in ('/admin/', '/api/', '/cart/', '/users/', '/orders/', '/seller/', '/kk/cart/', '/kk/users/'):
        assert f'Disallow: {path}\n' in body
    assert 'Disallow: /*?*sort=' in body
    assert 'Sitemap: http://testserver/sitemap.xml' in body
    # Сам каталог и товары не закрыты.
    assert 'Disallow: /\n' not in body
    assert 'Disallow: /product/' not in body


def test_sitemap_lists_active_products_in_both_languages(client, products):
    response = client.get('/sitemap.xml')

    assert response.status_code == 200
    body = response.content.decode()
    slug = products['active'].slug
    assert f'<loc>http://testserver/product/{slug}/</loc>' in body
    assert f'<loc>http://testserver/kk/product/{slug}/</loc>' in body
    assert 'hreflang="kk"' in body
    assert '<loc>http://testserver/</loc>' in body


def test_sitemap_excludes_inactive_products(client, products):
    body = client.get('/sitemap.xml').content.decode()

    assert products['hidden'].slug not in body
