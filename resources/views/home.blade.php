@extends('layouts.app')
@section('content')
<h1>Умный дом к Новому году!</h1>
<div style="display:flex;gap:20px;flex-wrap:wrap">
@foreach($products as $product)
    <div style="border:1px solid #ccc; padding:15px; width:250px">
        <img src="{{ $product->image }}" width="100%">
        <h3>{{ $product->name }}</h3>
        <p>{{ $product->price }} ₸</p>
        <form action="/{{ app()->getLocale() }}/cart/add" method="POST">
            @csrf
            <input type="hidden" name="id" value="{{ $product->id }}">
            <button type="submit">Купить</button>
        </form>
    </div>
@endforeach
</div>
@endsection