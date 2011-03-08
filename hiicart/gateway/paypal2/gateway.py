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

    def __init__(self, cart):
        super(Paypal2Gateway, self).__init__("paypal2", cart, default_settings)
        self._require_settings(["PASSWORD", "SIGNATURE", "USERID", "SELLER_EMAIL"])

    def _is_valid(self):
        """Return True if gateway is valid."""
        # TODO: Query Paypal to validate credentials
        return True

    def cancel_recurring(self):
        """Cancel recurring lineitem."""
        # TODO: Implement
        pass

    def charge_recurring(self, grace_period=None):
        """Charge a cart's recurring item, if necessary."""
        # TODO: Investigate if this is necessary. I think Paypal still
        #       takes care of the recurring charges.
        pass

    def sanitize_clone(self):
        """Nothing to do here..."""
        return self.cart

    def submit(self, collect_address=False, cart_settings_kwargs=None):
        """Submit the cart to the Paypal"""
        # NOTE: This is possible in Paypal, but I don't have time to
        #       implement it right now.
        self._update_with_cart_settings(self.cart, cart_settings_kwargs)
        if len(self.cart.one_time_lineitems) > 0 and len(self.cart.recurring_lineitems) > 0:
            raise Paypal2GatewayError("Recurring and Non-Recurring items can't be mixed.")
        result = api.set_express_checkout(self.cart, self.settings, collect_address)
        params = urllib.urlencode({"cmd": "_express-checkout",
                                   "token": result['TOKEN']})
        url = LIVE_REDIRECT if self.settings["LIVE"] else SANDBOX_REDIRECT
        return SubmitResult("url", "%s?%s" % (url, params))
