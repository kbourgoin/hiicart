import logging
import pprint
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt
from hiicart.gateway.amazon.ipn import AmazonIPN
from hiicart.gateway.base import GatewayError
from hiicart.gateway.countries import COUNTRIES
from hiicart.utils import format_exceptions, cart_by_uuid

log = logging.getLogger("hiicart.gateway.amazon")


def _find_cart(request_data):
    # Subscription payments look like '<uuid>-4' so grab the uuid id
    uuid = request_data["callerReference"][:36]
    return cart_by_uuid(uuid)


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
    cart = _find_cart(request.GET)
    handler = AmazonIPN(cart)
    handler._update_with_cart_settings(cart_settings_kwargs={'request': request})
    if not handler.verify_signature(request.GET.urlencode(), "GET", handler.settings["CBUI_RETURN_URL"]):
        log.error("Validation of Amazon request failed!")
        return HttpResponseRedirect(handler.settings.get("ERROR_RETURN_URL",
                                    handler.settings.get("RETURN_URL", "/")))
    if request.GET["status"] not in ("SA", "SB", "SC"):
        log.error("CBUI unsuccessful. Status code: %s" % request.GET["status"])
        return HttpResponseRedirect(handler.settings.get("CANCEL_RETURN_URL",
                                    handler.settings.get("RETURN_URL", "/")))
    if not cart:
        log.error("Unable to find cart.")
        return HttpResponseRedirect(handler.settings.get("ERROR_RETURN_URL",
                                    handler.settings.get("RETURN_URL", "/")))
    # Address collection. Any data already in cart is assumed correct
    cart.bill_first_name = cart.bill_first_name or request.GET.get("billingName", "")
    cart.ship_first_name = cart.ship_first_name or request.GET.get("addressName", "")
    cart.bill_street1 = cart.bill_street1 or request.GET.get("addressLine1", "")
    cart.ship_street1 = cart.ship_street1 or cart.bill_street1
    cart.bill_street2 = cart.bill_street1 or request.GET.get("addressLine2", "")
    cart.ship_street2 = cart.ship_street1 or cart.bill_street1
    cart.bill_state = cart.bill_state or request.GET.get("state", "")
    cart.ship_state = cart.ship_state or cart.bill_state
    cart.bill_postal_code = cart.bill_postal_code or request.GET.get("zip", "")
    cart.ship_postal_code = cart.ship_postal_code or cart.bill_postal_code
    country = request.GET.get("country", "").upper()
    cart.bill_country = cart.bill_country or COUNTRIES.get(country, "")
    cart.ship_country = cart.ship_country or cart.bill_country
    cart.bill_email = cart.bill_email = request.GET.get("buyerEmailAddress", "");
    cart.ship_email = cart.ship_email or cart.bill_email
    cart.save()
    recurring = cart.recurring_lineitems
    if len(recurring) > 0:
        handler.save_recurring_token(request.GET["tokenID"])
        if recurring[0].recurring_start is None:
            result = handler.make_pay_request(request.GET["tokenID"])
            if result == "Success":
                handler.begin_recurring()
        else:
            handler.begin_recurring()
    else:
        log.debug("Making pay request: %s" % request.GET['tokenID'])
        result = handler.make_pay_request(request.GET["tokenID"])
        log.debug("Pay request result: %s" % result)
    if 'RETURN_URL' in handler.settings:
        return HttpResponseRedirect(handler.settings['RETURN_URL'])
    return HttpResponseRedirect("/")


@csrf_view_exempt
@format_exceptions
@never_cache
def ipn(request):
    """Instant Payment Notification handler."""
    log.debug("IPN Received: \n%s" % pprint.pformat(dict(request.POST), indent=10))
    cart = _find_cart(request.POST)
    if not cart:
        raise GatewayError('amazon gateway: Unknown transaction')
    handler = AmazonIPN(cart)
    handler._update_with_cart_settings(cart_settings_kwargs={'request': request})
    if not handler.verify_signature(request.POST.urlencode(), "POST", handler.settings["IPN_URL"]):
        log.error("Validation of Amazon request failed!")
        return HttpResponseBadRequest("Validation of Amazon request failed!")
    if not cart:
        log.error("Unable to find cart.")
        return HttpResponseBadRequest()
    if request.POST["notificationType"] == "TransactionStatus":
        handler.accept_payment(request.POST)
    elif request.POST["notificationType"] == "TokenCancellation":
        handler.end_recurring(request.POST.get("tokenId", None))
    return HttpResponse()
