import hiicart.gateway.paypal_adaptive.views

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'authorized/?$',          'hiicart.gateway.paypal2.views.authorized'),
    (r'do_pay/?$',              'hiicart.gateway.paypal2.views.do_pay'),
    (r'ipn/?$',                 'hiicart.gateway.paypal2.views.ipn'),
)
