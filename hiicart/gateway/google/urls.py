import hiicart.gateway.google.views

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'ipn/?$',                                    'hiicart.gateway.google.views.ipn'),
)
