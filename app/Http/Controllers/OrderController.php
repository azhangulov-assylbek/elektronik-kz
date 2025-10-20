<?php
namespace App\Http\Controllers;
use Illuminate\Http\Request;

class OrderController extends Controller
{
    public function create($locale)
    {
        app()->setLocale($locale);
        $cart = session('cart', []);
        return view('checkout', compact('cart'));
    }

    public function store(Request $request, $locale)
    {
        // Здесь будет отправка в CJ API
        session()->forget('cart');
        return redirect("/$locale/success")->with('message', 'Заказ оформлен!');
    }
}