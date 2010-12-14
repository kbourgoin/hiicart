import hiicart.gateway.paypal.views

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'ipn/?$',                                    'hiicart.gateway.paypal.views.ipn'),
)
