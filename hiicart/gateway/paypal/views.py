import logging

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt

from hiicart.gateway.paypal.ipn import PaypalIPN
from hiicart.gateway.paypal.errors import PaypalGatewayError
from hiicart.models import HiiCart, Payment
from hiicart.utils import format_exceptions

log = logging.getLogger("hiicart.gateway.paypal")

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
    data = request.POST
    log.info("IPN Notification received from Paypal: %s" % data)
    # Verify the data with Paypal
    handler = PaypalIPN()
    if not handler.confirm_ipn_data(request.raw_post_data):
        log.error("Paypal IPN Confirmation Failed.")
        raise PaypalGatewayError("Paypal IPN Confirmation Failed.")
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
