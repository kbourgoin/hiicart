import braintree
import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_view_exempt
from hiicart.gateway.base import GatewayError
from hiicart.gateway.braintree.gateway import BraintreeGateway
from hiicart.gateway.braintree.ipn import BraintreeIPN
from hiicart.utils import format_exceptions, call_func, cart_by_uuid


log = logging.getLogger("hiicart.gateway.braintree")


def _find_cart(result):
    """Find purchase using the Braintree result"""
    if result.transaction.order_id:
        return cart_by_uuid(result.transaction.order_id)

    log.error("Could not find order ID in Braintree result: %s" % str(data.items()))
    return None


@csrf_view_exempt
@format_exceptions
@never_cache
def payment(request, cart_uuid):
    """View to receive payment result from Braintree"""
    data = request.META["QUERY_STRING"]
    log.info("Payment result received from Braintree: %s" % data)
    cart = cart_by_uuid(cart_uuid)
    if cart:
        gateway = BraintreeGateway(cart)
        handler = BraintreeIPN(cart)
        handler.confirm_payment(data)
        return redirect(gateway.store_return_url(request))
    