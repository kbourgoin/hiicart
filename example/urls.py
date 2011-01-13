import hiicart.urls

from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^/?$', 'apps.basic.views.index'),
    (r'^paypal_receipt/?$', 'apps.basic.views.paypal_receipt'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^hiicart/', include(hiicart.urls)),
)
