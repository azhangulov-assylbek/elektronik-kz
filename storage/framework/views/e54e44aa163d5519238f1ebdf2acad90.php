<!DOCTYPE html>
<html lang="<?php echo e(app()->getLocale()); ?>">
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
        <a href="/<?php echo e(app()->getLocale()); ?>">Главная</a>
        <a href="/<?php echo e(app()->getLocale()); ?>/checkout">Корзина (<?php echo e(array_sum(session('cart', []))); ?>)</a>
        <?php if(app()->getLocale() == 'ru'): ?>
            <a href="/kk">Қазақша</a>
        <?php else: ?>
            <a href="/ru">Русский</a>
        <?php endif; ?>
    </nav>
    <main>
        <?php echo $__env->yieldContent('content'); ?>
    </main>
</body>
</html><?php /**PATH C:\Users\azhan\Desktop\elektronik-kz\resources\views/layouts/app.blade.php ENDPATH**/ ?>