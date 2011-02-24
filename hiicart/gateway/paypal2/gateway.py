"""Paypal2 -- Website Payments Pro Gateway

Please note that currently only Express Checkout is implemented.
Direct Payment can be supported in the future, but requires reworking
of core HiiCart models so they can use credit card numbers as required.
"""

import urllib

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult
from hiicart.gateway.paypal2 import api
from hiicart.gateway.paypal2.errors import Paypal2GatewayError
from hiicart.gateway.paypal2.settings import SETTINGS as default_settings

LIVE_REDIRECT = "https://www.paypal.com/cgi-bin/webscr"
SANDBOX_REDIRECT = "https://www.sandbox.paypal.com/cgi-bin/webscr"

class Paypal2Gateway(PaymentGatewayBase):
    """Payment Gateway for Paypal Website Payments Pro."""

    def __init__(self):
        super(Paypal2Gateway, self).__init__("paypal2", default_settings)
        self._require_settings(["PASSWORD", "SIGNATURE", "USERID", "SELLER_EMAIL"])

    def _is_valid(self):
        """Return True if gateway is valid."""
        # TODO: Query Paypal to validate credentials
        return True

    def cancel_recurring(self, cart):
        """Cancel recurring lineitem."""
        # TODO: Implement
        pass

    def charge_recurring(self, cart, grace_period=None):
        """Charge a cart's recurring item, if necessary."""
        # TODO: Investigate if this is necessary. I think Paypal still
        #       takes care of the recurring charges.
        pass

    def sanitize_clone(self, cart):
        """Nothing to do here..."""
        return cart

    def submit(self, cart, collect_address=False):
        """Submit the cart to the Paypal"""
        # NOTE: This is possible in Paypal, but I don't have time to
        #       implement it right now.
        if len(cart.one_time_lineitems) > 0 and len(cart.recurring_lineitems) > 0:
            raise Paypal2GatewayError("Recurring and Non-Recurring items can't be mixed.")
        self._update_with_cart_settings(cart)
        result = api.set_express_checkout(cart, self.settings, collect_address)
        params = urllib.urlencode({"cmd": "_express-checkout",
                                   "token": result['TOKEN']})
        url = LIVE_REDIRECT if self.settings["LIVE"] else SANDBOX_REDIRECT
        return SubmitResult("url", "%s?%s" % (url, params))
