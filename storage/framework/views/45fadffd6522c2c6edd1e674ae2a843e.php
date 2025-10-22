
<?php $__env->startSection('content'); ?>
<h1>Умный дом к Новому году!</h1>
<div style="display:flex;gap:20px;flex-wrap:wrap">
<?php $__currentLoopData = $products; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $product): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
    <div style="border:1px solid #ccc; padding:15px; width:250px">
        <img src="<?php echo e($product->image); ?>" width="100%">
        <h3><?php echo e($product->name); ?></h3>
        <p><?php echo e($product->price); ?> ₸</p>
        <form action="/<?php echo e(app()->getLocale()); ?>/cart/add" method="POST">
            <?php echo csrf_field(); ?>
            <input type="hidden" name="id" value="<?php echo e($product->id); ?>">
            <button type="submit">Купить</button>
        </form>
    </div>
<?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
</div>
<?php $__env->stopSection(); ?>
<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH C:\Users\azhan\Desktop\elektronik-kz\resources\views/home.blade.php ENDPATH**/ ?>