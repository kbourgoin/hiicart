from django.conf import settings
from django.shortcuts import render_to_response
from pprint import PrettyPrinter

from hiicart import validate_gateway

def index(request):
    p = PrettyPrinter(width=40)
    context = {
        'paypal': (p.pformat(settings.HIICART_SETTINGS['PAYPAL']),
                   validate_gateway('paypal')),
        'paypal2': (p.pformat(settings.HIICART_SETTINGS['PAYPAL2']),
                   validate_gateway('paypal2')),
        'paypal_adaptive': (p.pformat(settings.HIICART_SETTINGS['PAYPAL_ADAPTIVE']),
                   validate_gateway('paypal_adaptive')),
        'google': (p.pformat(settings.HIICART_SETTINGS['GOOGLE']),
                   validate_gateway('google')),
        'amazon': (p.pformat(settings.HIICART_SETTINGS['AMAZON']),
                   validate_gateway('amazon')),
        }
    return render_to_response('index.html', context)
