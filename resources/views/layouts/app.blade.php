<!DOCTYPE html>
<html lang="{{ app()->getLocale() }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>elektronik.kz</title>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-XXXXXXXXXX'); // ← замени на свой GA4 ID
    </script>
</head>
<body>
    <nav>
        <a href="/{{ app()->getLocale() }}">Главная</a>
        <a href="/{{ app()->getLocale() }}/checkout">Корзина ({{ array_sum(session('cart', [])) }})</a>
        @if(app()->getLocale() == 'ru')
            <a href="/kk">Қазақша</a>
        @else
            <a href="/ru">Русский</a>
        @endif
    </nav>
    <main>
        @yield('content')
    </main>
</body>
</html>