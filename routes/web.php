<?php
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\HomeController;
use App\Http\Controllers\ProductController;
use App\Http\Controllers\OrderController;

Route::group(['prefix' => '{locale}', 'where' => ['locale' => '[a-z]{2}']], function () {
    Route::get('/', [HomeController::class, 'index']);
    Route::get('/product/{id}', [ProductController::class, 'show']);
    Route::post('/cart/add', [ProductController::class, 'addToCart']);
    Route::get('/checkout', [OrderController::class, 'create']);
    Route::post('/order', [OrderController::class, 'store']);
    Route::get('/success', fn($locale) => view('success'));
});

Route::get('/', fn() => redirect('/ru'));