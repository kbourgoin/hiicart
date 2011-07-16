import hiicart.gateway.google.views

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'payment/(?P<cart_uuid>[-\w]+)/?$',		'hiicart.gateway.braintree.views.payment'),
)
