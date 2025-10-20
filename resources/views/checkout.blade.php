@extends('layouts.app')
@section('content')
<h1>{{ __('common.checkout') }}</h1>
<form method="POST" action="/{{ app()->getLocale() }}/order">
    @csrf
    <p><input name="name" placeholder="{{ __('common.name') }}" required></p>
    <p><input name="phone" placeholder="{{ __('common.phone') }}" required></p>
    <p><textarea name="address" placeholder="{{ __('common.address') }}" required></textarea></p>
    <button type="submit">{{ __('common.submit') }}</button>
</form>
@endsection