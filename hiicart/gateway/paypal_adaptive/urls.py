import hiicart.gateway.paypal_adaptive.views

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'ipn/?$',                                    'hiicart.gateway.paypal_adaptive.views.ipn'),
)
