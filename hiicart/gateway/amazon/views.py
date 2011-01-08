import logging
import pprint
import xml.etree.cElementTree as ET

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt

from hiicart.gateway.amazon import fps
from hiicart.gateway.amazon.ipn import AmazonIPN 
from hiicart.gateway.countries import COUNTRIES
from hiicart.models import HiiCart
from hiicart.utils import format_exceptions

log = logging.getLogger("hiicart.gateway.amazon")

def _find_cart(request_data):
    try:
        # Subscription payments look like '<uuid>-4' so grab the uuid id
        uuid = request_data["callerReference"][:36]
        return HiiCart.objects.get(_cart_uuid=uuid)
    except HiiCart.DoesNotExist:
        return None

@csrf_view_exempt
@format_exceptions
@never_cache
def cbui(request, settings=None):
    """
    View used when the Co-Branded UI returns.

    This view verifies that the CBUI returned successfully and
    uses the provided authorization to initiate a Pay request.
    """
    log.debug("CBUI Received: \n%s" % pprint.pformat(dict(request.GET), indent=10))
    handler = AmazonIPN()
    cart = _find_cart(request.GET)
    if not handler.verify_signature(request.GET.urlencode(), "GET", handler.settings["CBUI_RETURN_URL"], cart):
        log.error("Validation of Amazon request failed!")
        return HttpResponseRedirect(handler.settings.get("ERROR_RETURN_URL",
                                    handler.settings.get("RETURN_URL", "/")))
    if request.GET["status"] not in ("SA", "SB", "SC"):
        log.error("CBUI unsuccessful. Status code: %s" % request.GET["status"])
        return HttpResponseRedirect(handler.settings.get("CANCEL_RETURN_URL",
                                    handler.settings.get("RETURN_URL", "/")))
    if not cart:
        log.error("Unable to find HiiCart.")
        return HttpResponseRedirect(handler.settings.get("ERROR_RETURN_URL",
                                    handler.settings.get("RETURN_URL", "/")))
    # Address collection. Any data already in cart is assumed correct
    name = request.GET.get("addressName", "").split(" ")
    cart.first_name = cart.first_name or name[0]
    if len(name) > 1:
        cart.last_name = cart.last_name or name[1]
    cart.bill_street1 = cart.bill_street1 or request.GET.get("addressLine1", "")
    cart.bill_street2 = cart.bill_street1 or request.GET.get("addressLine2", "")
    cart.bill_state = cart.bill_state or request.GET.get("state", "")
    cart.bill_postal_code = cart.bill_postal_code or request.GET.get("zip", "")
    country = request.GET.get("country", "").upper()
    if not cart.bill_country and country in COUNTRIES.values():
        cart.bill_country = [k for k,v in COUNTRIES.iteritems() if v == country][0]
    cart.save()
    recurring = cart.recurringlineitems.all()
    if len(recurring) > 0:
        handler.save_recurring_token(cart, request.GET["tokenID"])
        if recurring[0].recurring_start is None:
            result = handler.make_pay_request(cart, request.GET["tokenID"]) 
            if result == "Success":
                handler.begin_recurring(cart)
        else:
            handler.begin_recurring(cart)
    else:
        result = handler.make_pay_request(cart, request.GET["tokenID"])
    if 'RETURN_URL' in handler.settings:
        return HttpResponseRedirect(handler.settings['RETURN_URL'])
    return HttpResponseRedirect("/")

@csrf_view_exempt
@format_exceptions
@never_cache
def ipn(request):
    """Instant Payment Notification handler."""
    log.debug("IPN Received: \n%s" % pprint.pformat(dict(request.POST), indent=10))
    handler = AmazonIPN()
    cart = _find_cart(request.POST)
    if not handler.verify_signature(request.POST.urlencode(), "POST", handler.settings["IPN_URL"], cart):
        log.error("Validation of Amazon request failed!")
        return HttpResponse("Validation of Amazon request failed!")
    cart = _find_cart(request.POST)
    if not cart:
        log.error("Unable to find HiiCart.")
        return HttpResponse()
    if request.POST["notificationType"] == "TransactionStatus":
        handler.accept_payment(cart, request.POST)
    elif request.POST["notificationType"] == "TokenCancellation":
        handler.end_recurring(cart, request.POST.get("tokenId", None))
    return HttpResponse()
