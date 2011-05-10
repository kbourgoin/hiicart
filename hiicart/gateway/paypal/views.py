import logging
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt
from hiicart.gateway.base import GatewayError
from hiicart.gateway.paypal.ipn import PaypalIPN
from hiicart.utils import format_exceptions, cart_by_uuid
from urllib import unquote_plus
from urlparse import parse_qs


log = logging.getLogger("hiicart.gateway.paypal")


def _find_cart(data):
    # invoice may have a suffix due to retries
    invoice = data.get('invoice') or data.get('item_number')
    if not invoice:
        log.warn("No invoice # in data, aborting IPN")
        return None

    return cart_by_uuid(invoice[:36])


@csrf_view_exempt
@format_exceptions
@never_cache
def ipn(request):
    """
    PayPal IPN (Instant Payment Notification)

    Confirms that payment has been completed and marks invoice as paid.
    Adapted from IPN cgi script provided at:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/456361
    """
    if request.method != "POST":
        return HttpResponse("Requests must be POSTed")
    data = request.POST.copy()
    log.info("IPN Notification received from Paypal: %s" % data)
    try:
        log.info("IPN Notification received from Paypal (raw): %s" % request.raw_post_data)
    except:
        pass
    # Verify the data with Paypal
    cart = _find_cart(data)
    if not cart:
        raise GatewayError('paypal gateway: Unknown transaction')
    handler = PaypalIPN(cart)
    if not handler.confirm_ipn_data(request.raw_post_data):
        log.error("Paypal IPN Confirmation Failed.")
        raise GatewayError("Paypal IPN Confirmation Failed.")
    # Paypal defaults to cp1252, because it hates you
    # So, if we end up with the unicode char that means
    # "unknown char" (\ufffd), try to transcode from cp1252
    parsed_raw = parse_qs(request.raw_post_data)
    for key, value in data.iteritems():
        if u'\ufffd' in value:
            try:
                data.update({key: unicode(unquote_plus(parsed_raw[key][-1]), 'cp1252')})
            except:
                pass
    txn_type = data.get("txn_type", "")
    status = data.get("payment_status", "unknown")
    if txn_type == "subscr_cancel" or txn_type == "subscr_eot":
        handler.cancel_subscription(data)
    elif txn_type == "subscr_signup":
        handler.activate_subscription(data)
    elif status == "Completed":
        handler.accept_payment(data)
    else:
        log.info("Unknown IPN type or status. Type: %s\tStatus: %s" %
                 (status, txn_type))
    return HttpResponse()
