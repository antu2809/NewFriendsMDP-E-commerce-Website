from django import forms
from .models import Product, CreditCard, PaymentMethod

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'description', 'price', 'stock', 'image')

class PaymentForm(forms.ModelForm):
    otp_code = forms.CharField(label='OTP Code')  # Campo para ingresar el código de verificación
    payment_method = forms.ModelChoiceField(queryset=PaymentMethod.objects.all(), empty_label=None)
    credit_card_number = forms.CharField(label='Credit Card Number', required=False)
    credit_card_expiration_date = forms.DateField(label='Credit Card Expiration Date', required=False)
    credit_card_cvv = forms.CharField(label='Credit Card CVV', required=False)
    
    debit_card_number = forms.CharField(label='Debit Card Number', required=False)
    debit_card_expiration_date = forms.DateField(label='Debit Card Expiration Date', required=False)
    debit_card_cvv = forms.CharField(label='Debit Card CVV', required=False)
    
    class Meta:
        model = CreditCard
        fields = ['otp_code', 'payment_method', 'credit_card_number', 'credit_card_expiration_date',
                  'credit_card_cvv', 'debit_card_number', 'debit_card_expiration_date', 'debit_card_cvv']

