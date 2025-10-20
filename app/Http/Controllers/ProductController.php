<?php
namespace App\Http\Controllers;
use Illuminate\Http\Request;

class ProductController extends Controller
{
    public function show($locale, $id)
    {
        app()->setLocale($locale);
        $product = (object)['id' => $id, 'name' => __('common.smart_lamp'), 'price' => 12000, 'description' => __('common.lamp_desc')];
        return view('product', compact('product'));
    }

    public function addToCart(Request $request)
    {
        $cart = session()->get('cart', []);
        $cart[$request->id] = ($cart[$request->id] ?? 0) + 1;
        session()->put('cart', $cart);
        return back()->with('success', 'Товар добавлен в корзину!');
    }
}