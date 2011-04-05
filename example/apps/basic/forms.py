from decimal import Decimal
from django import forms

from hiicart import validate_gateway

GATEWAYS = (
        ('amazon', 'amazon'),
        ('google', 'google'),
        ('paypal', 'paypal'),
        ('paypal2', 'paypal2'),
        ('paypal_adaptive', 'paypal_adaptive'),
        )

PANTS = {'unit_price': Decimal('19.99'), 'description': 'Some very fancy pants',
         'name': 'Fancypants!', 'sku': '1', 'thankyou': 'Thanks for buying pants!'}
MONKEYBUTLER = {'unit_price': Decimal('100.00'), 'description': 'A moneky trained as a butler',
                'name': 'Monkey Butler', 'sku': '2', 'thankyou': "Really? You're buying a monkey?"}
SUBSCRIPTION = {'recurring_price': Decimal('5.00'), 'duration': 1, 'duration_unit': 'MONTH',
                'description': 'A newsletter subscription', 'name': 'Newsletter Subscription',
                'sku': '3', 'thankyou': 'Thanks for the subscription'}

class BasicPurchaseForm(forms.Form):
    fancypants = forms.BooleanField(required=False)
    monkeybutler = forms.BooleanField(required=False)
    subscription = forms.BooleanField(required=False)
    gateway = forms.CharField(required=True, widget=forms.Select(choices=GATEWAYS))

    def clean(self):
        if not (self.cleaned_data['fancypants'] or self.cleaned_data['monkeybutler'] or self.cleaned_data['subscription']):
            raise forms.ValidationError('Please select something to buy!')
        return self.cleaned_data

    def clean_gateway(self):
        if validate_gateway(self.cleaned_data['gateway']) != True:
            raise forms.ValidationError('Gateway not properly set up.')
        return self.cleaned_data['gateway']

class PaypalReceiptForm(forms.Form):
    token = forms.CharField(required=True, widget=forms.HiddenInput)
    PayerID = forms.CharField(required=True, widget=forms.HiddenInput)
    cart = forms.CharField(required=True, widget=forms.HiddenInput)
