<?php
namespace App\Http\Controllers;
use Illuminate\Http\Request;

class HomeController extends Controller
{
    public function index($locale)
    {
        app()->setLocale($locale);
        // Позже замени на реальные товары из CJ
        $products = [
            (object)['id' => 1, 'name' => __('common.smart_lamp'), 'price' => 12000, 'image' => 'https://via.placeholder.com/300?text=Smart+Lamp'],
            (object)['id' => 2, 'name' => __('common.smart_socket'), 'price' => 11000, 'image' => 'https://via.placeholder.com/300?text=Smart+Socket'],
        ];
        return view('home', compact('products'));
    }
}