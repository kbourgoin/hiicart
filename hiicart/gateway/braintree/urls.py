import hiicart.gateway.google.views

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'payment/?$',		'hiicart.gateway.braintree.views.payment'),
)
