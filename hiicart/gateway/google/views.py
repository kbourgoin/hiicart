import base64
import hashlib
import hmac
import httplib2
import logging
import xml.etree.cElementTree as ET

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt

from hiicart.gateway.base import GatewayError
from hiicart.gateway.google.gateway import GoogleGateway
from hiicart.gateway.google.ipn import GoogleIPN
from hiicart.utils import format_exceptions, call_func

log = logging.getLogger("hiicart.gateway.google")

@csrf_view_exempt
@format_exceptions
@never_cache
def ipn(request):
    """View to receive notifications from Google"""
    if request.method != "POST":
        return HttpResponseBadRequest("Requests must be POSTed")
    data = request.POST
    log.info("IPN Notification received from Google Checkout: %s" % data)
    # Check credentials
    gateway = GoogleGateway()
    if gateway.settings.get("IPN_AUTH_VALS", False):
        mine = call_func(gateway.settings["IPN_AUTH_VALS"])
    else:
        mine = gateway.get_basic_auth()
    theirs = request.META["HTTP_AUTHORIZATION"].split(" ")[1]
    if theirs not in mine:
        response = HttpResponse("Authorization Required")
        response["WWW-Authenticate"] = "Basic"
        response.status_code = 401
        return response
    # Handle the notification
    type = data["_type"]
    handler = GoogleIPN()
    if type == "new-order-notification":
        handler.new_order(data)
    elif type == "order-state-change-notification":
        handler.order_state_change(data)
    elif type == "risk-information-notification":
        handler.risk_information(data)
    elif type == "charge-amount-notification":
        handler.charge_amount(data)
    elif type == "refund-amount-notification":
        handler.refund_amount(data)
    elif type == "chargeback-amount-notification":
        handler.chargeback_amount(data)
    elif type == "authorization-amount-notification":
        handler.authorization_amount(data)
    elif type == "cancelled-subscription-notification":
        handler.cancelled_subscription(data)
    else:
        raise GatewayError("google gateway: Unknown message type recieved: %s" % type)
    # Return ack so google knows we handled the message
    ack = "<notification-acknowledgment xmlns='http://checkout.google.com/schema/2' serial-number='%s'/>" %  data["serial-number"].strip()
    response = HttpResponse(content=ack, content_type="text/xml; charset=UTF-8")
    log.debug("Google Checkout: Sending IPN Acknowledgement")
    return response
