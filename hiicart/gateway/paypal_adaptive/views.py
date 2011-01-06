import logging
import pprint
import xml.etree.cElementTree as ET

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt

from hiicart.gateway.base.models import GatewayError
from hiicart.gateway.paypal_adaptive.ipn import PaypalAPIPN
from hiicart.models import HiiCart
from hiicart.utils import format_exceptions

log = logging.getLogger("hiicart.gateway.paypal_adaptive")

def _find_cart(data):
    pass

@csrf_view_exempt
@format_exceptions
@never_cache
def ipn(request):
    """Instant Payment Notification ipn.
    
    There is currently not working documentation on Paypal's site
    for IPNs from the Adaptive Payments API.  This has been created using
    test messages from AP and knowledge from the web payments API."""
    if request.method != "POST":
        return HttpResponse("Requests must be POSTed")
    data = request.POST
    log.info("IPN Notification received from Paypal: %s" % data)
    # Verify the data with Paypal
    ipn = PaypalAPIPN()
    if not ipn.confirm_ipn_data(request.raw_post_data):
        log.error("Paypal IPN Confirmation Failed.")
        raise GatewayError("Paypal IPN Confirmation Failed.")
    if "transaction_type" in data: # Parallel/Chained Payment initiation IPN.
        if data["transaction_type"] == "Adaptive Payment PAY":
            ipn.accept_adaptive_payment(data)
        else:
            log.info("Unknown txn_type: %s" % data["txn_type"])
    elif "txn_type" in data: # Inidividual Tranasction IPN
        if data["txn_type"] == "web_accept":
            ipn.accept_payment(data)
        else:
            log.info("Unknown txn_type: %s" % data["txn_type"])
    else: #dunno
        log.error("transaction_type not in IPN data.")
        raise GatewayError("transaction_type not in IPN.")
    return HttpResponse()
