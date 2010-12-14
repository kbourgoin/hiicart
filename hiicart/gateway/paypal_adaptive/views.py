import logging
import pprint
import xml.etree.cElementTree as ET

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt

from hiicart.gateway.paypal_adaptive.errors import PaypalAdaptivePaymentsGatewayError
from hiicart.gateway.paypal_adaptive.ipn import PaypalAdaptivePaymentsIPN
from hiicart.models import HiiCart
from hiicart.utils import format_exceptions

log = logging.getLogger("hiicart.gateway.paypal_adaptive")

def _find_cart(data):
    pass

@csrf_view_exempt
@format_exceptions
@never_cache
def ipn(request):
    """Instant Payment Notification handler."""
    log.debug("IPN Received: \n%s" % pprint.pformat(
        dict(request.POST), indent=10))
    #handler = PaypalAdaptivePaymentsIPN()
    #cart = _find_cart(request.POST)
    return HttpResponse()
