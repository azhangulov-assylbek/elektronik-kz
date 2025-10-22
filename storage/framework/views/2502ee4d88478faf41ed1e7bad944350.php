
<?php $__env->startSection('content'); ?>
<h1><?php echo e(__('common.checkout')); ?></h1>
<form method="POST" action="/<?php echo e(app()->getLocale()); ?>/order">
    <?php echo csrf_field(); ?>
    <p><input name="name" placeholder="<?php echo e(__('common.name')); ?>" required></p>
    <p><input name="phone" placeholder="<?php echo e(__('common.phone')); ?>" required></p>
    <p><textarea name="address" placeholder="<?php echo e(__('common.address')); ?>" required></textarea></p>
    <button type="submit"><?php echo e(__('common.submit')); ?></button>
</form>
<?php $__env->stopSection(); ?>
<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH C:\Users\azhan\Desktop\elektronik-kz\resources\views/checkout.blade.php ENDPATH**/ ?>