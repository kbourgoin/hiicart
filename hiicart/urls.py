import hiicart.gateway.amazon.urls
import hiicart.gateway.google.urls
import hiicart.gateway.paypal.urls

from django.conf.urls.defaults import *

urlpatterns = patterns('',  
    (r'complete/?$',                                    'hiicart.views.complete'),
    (r'^amazon/',                                       include(hiicart.gateway.amazon.urls)),
    (r'^google/',                                       include(hiicart.gateway.google.urls)),
    (r'^paypal/',                                       include(hiicart.gateway.paypal.urls)),
)
