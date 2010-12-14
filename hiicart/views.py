from django.conf import settings
from django.http import HttpResponseRedirect

from hiicart.models import HiiCart

def complete(request):
    """View to handle redirection after a cart is completed."""
    next = settings.HIICART_SETTINGS.get("CART_COMPLETE", "/")
    cartid = request.session.get("cartid", None)
    if cartid:
        cart = HiiCart.objects.get(pk=cartid)
        next = cart.success_url if cart.success_url else next
        if cart.failure_url and request.GET.get("fail", None) == "1":
            next = cart.failure_url
    return HttpResponseRedirect(next)
