from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from hiicart import validate_gateway
from hiicart.gateway.base import SubmitResult
from hiicart.models import *
from pprint import PrettyPrinter

from apps.basic import forms

def index(request):
    context = {}
    if request.method == 'POST':
        form = forms.BasicPurchaseForm(request.POST)
        if form.is_valid():
            cart = HiiCart.objects.create()
            if form.cleaned_data['fancypants']:
                LineItem.objects.create(cart=cart, quantity=1, **forms.PANTS)
            if form.cleaned_data['monkeybutler']:
                LineItem.objects.create(cart=cart, quantity=1, **forms.MONKEYBUTLER)
            if form.cleaned_data['subscription']:
                RecurringLineItem.objects.create(cart=cart, quantity=1, **forms.SUBSCRIPTION)
            result = cart.submit(form.cleaned_data['gateway'])
            if result.type == 'url':
                return HttpResponseRedirect(result.url)
            else:
                return HttpResponseRedirect('/paypal_redirect')
    else:
        form = forms.BasicPurchaseForm()
    p = PrettyPrinter(width=40)
    context['paypal'] = (p.pformat(settings.HIICART_SETTINGS['PAYPAL']),
                         validate_gateway('paypal'))
    context['paypal2'] = (p.pformat(settings.HIICART_SETTINGS['PAYPAL2']),
                          validate_gateway('paypal2'))
    context['paypal_adaptive'] = (p.pformat(settings.HIICART_SETTINGS['PAYPAL_ADAPTIVE']),
                                  validate_gateway('paypal_adaptive'))
    context['google'] = (p.pformat(settings.HIICART_SETTINGS['GOOGLE']),
                         validate_gateway('google'))
    context['amazon'] = (p.pformat(settings.HIICART_SETTINGS['AMAZON']),
                         validate_gateway('amazon'))
    context['form'] = form
    return render_to_response('index.html', context)

def paypal_receipt(request):
    if 'cart' not in request.GET:
        return HttpResponseRedirect('/')
    context = {
            'form' :  forms.PaypalReceiptForm(request.GET),
            'cart': HiiCart.objects.get(_cart_uuid=request.GET['cart']),
            }
    return render_to_response('paypal_receipt.html', context)
