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


@csrf_view_exempt
@format_exceptions
@never_cache
def payment(request):
    """View to receive payment result from Braintree"""
    data = request.META["QUERY_STRING"]
    log.info("Payment result received from Braintree: %s" % data)
    result = braintree.TransparentRedirect.confirm(data)
    cart = cart_by_uuid(result.transaction.order_id)
    if cart:
        gateway = BraintreeGateway(cart)
        if result.is_success:
            handler = BraintreeIPN(cart)
            created = handler.create_payment(result.transaction)
            if created:
                return redirect(gateway.store_return_url(request))
        # On failure, redirect back to the payment form
        return redirect(gateway.store_return_url(request))
    # If we couldn't find a cart, something went horribly wrong
    log.error("Could not find cart associated with payment (%s, " % (result.transaction.id, result.transaction.order_id))