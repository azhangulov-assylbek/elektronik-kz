from django import forms

from payments.models import Payment

from .models import Order


class CheckoutForm(forms.ModelForm):
    payment_method = forms.ChoiceField(choices=Payment.Method.choices, label='Способ оплаты')

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'city', 'street', 'house', 'apartment', 'payment_method', 'comment']
