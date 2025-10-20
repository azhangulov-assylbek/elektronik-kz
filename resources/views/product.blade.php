@extends('layouts.app')
@section('content')
<h1>{{ $product->name }}</h1>
<img src="https://via.placeholder.com/400" width="100%">
<p>{{ $product->description }}</p>
<p><strong>{{ $product->price }} ₸</strong></p>
<form action="/{{ app()->getLocale() }}/cart/add" method="POST">
    @csrf
    <input type="hidden" name="id" value="{{ $product->id }}">
    <button type="submit">{{ __('common.buy') }}</button>
</form>
@endsection