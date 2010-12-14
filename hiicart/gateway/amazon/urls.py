import hiicart.gateway.amazon.views

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'cbui/?$',                                   'hiicart.gateway.amazon.views.cbui'),
    (r'ipn/?$',                                    'hiicart.gateway.amazon.views.ipn'),
)

