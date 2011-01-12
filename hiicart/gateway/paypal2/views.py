import logging
import pprint
import urllib

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt

from hiicart.gateway.base import GatewayError
from hiicart.gateway.paypal2 import api
from hiicart.gateway.paypal2.ipn import Paypal2IPN
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
    import pdb; pdb.set_trace()
    if request.method != "POST":
        return HttpResponse("Requests must be POSTed")
    data = request.POST
    log.info("IPN Notification received from Paypal: %s" % data)
    # Verify the data with Paypal
    ipn = Paypal2IPN()
    if not ipn.confirm_ipn_data(request.raw_post_data):
        log.error("Paypal IPN Confirmation Failed.")
        raise GatewayError("Paypal IPN Confirmation Failed.")
    if "txn_type" in data: # Inidividual Tranasction IPN
        if data["txn_type"] == "cart":
            ipn.accept_payment(data)
        else:
            log.info("Unknown txn_type: %s" % data["txn_type"])
    else: #dunno
        log.error("transaction_type not in IPN data.")
        raise GatewayError("transaction_type not in IPN.")
    return HttpResponse()

@csrf_view_exempt
@format_exceptions
@never_cache
def authorized(request):
    if "token" not in request.GET:
        raise Http404
    ipn = Paypal2IPN()
    info = api.get_express_details(request.GET["token"], ipn.settings)
    params = request.GET.copy()
    params["cart"] = info["INVNUM"]
    url = "%s?%s" % (ipn.settings["RECEIPT_URL"], urllib.urlencode(params))
    import pdb; pdb.set_trace()
    return HttpResponseRedirect(url)

@csrf_view_exempt
@format_exceptions
@never_cache
def do_pay(request):
    if "token" not in request.POST or "PayerID" not in request.POST \
        or "cart" not in request.POST:
            raise GatewayError("Incorrect values POSTed to do_buy")
    cart = HiiCart.objects.get(_cart_uuid=request.POST["cart"])
    ipn = Paypal2IPN()
    if cart.lineitems.count() > 0:
        api.do_express_payment(request.POST["token"], request.POST["PayerID"],
                               cart, ipn.settings)
    if cart.recurringlineitems.count() > 0:
        api.create_recurring_profile(request.POST["token"],
                                     request.POST["PayerID"],
                                     cart, ipn.settings)
    # TODO: Redirect to HiiCart complete URL
    return HttpResponseRedirect("/")
