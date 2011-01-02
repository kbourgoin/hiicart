"""Paypal2 -- Website Payments Pro Gateway

Please note that currently only Express Checkout is implemented.
Direct Payment can be supported in the future, but requires reworking
of core HiiCart models so they can use credit card numbers as required.
"""

import httplib2
import urllib

from decimal import Decimal
from django.core.urlresolvers import reverse
from urllib import unquote

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult
from hiicart.gateway.paypal2.errors import Paypal2GatewayError
from hiicart.gateway.paypal2.settings import default_settings

LIVE_ENDPOINT = "https://api-3t.paypal.com/nvp"
LIVE_REDIRECT = "https://www.paypal.com/cgi-bin/webscr"
SANDBOX_ENDPOINT = "https://api-3t.sandbox.paypal.com/nvp"
SANDBOX_REDIRECT = "https://www.sandbox.paypal.com/cgi-bin/webscr"

class Paypal2Gateway(PaymentGatewayBase):
    """Payment Gateway for Paypal Website Payments Pro."""

    def __init__(self):
        super(Paypal2Gateway, self).__init__(
                "paypal2", default_settings)

    @property
    def ipn_url(self):
        if "IPN_URL" not in self.settings:
            if "BASE_URL" not in self.settings:
                raise Paypal2GatewayError(
                        "Either IPN_URL or BASE_URL is required.")
            # Avoid circular import
            from hiicart.gateway.paypal2.views import ipn
            return "%s%s" % (self.settings["BASE_URL"], reverse(ipn))
        else:
            return self.settings["IPN_URL"]

    def _send_command(self, params):
        keys = params.keys()
        keys.sort()
        pairs = [(k,params[k]) for k in keys]
        url = LIVE_ENDPOINT if self.settings["LIVE"] else SANDBOX_ENDPOINT
        response, data = httplib2.Http().request(url, "POST",
                                                 urllib.urlencode(pairs))
        data = unquote(data)
        # TODO: logging
        return dict([(l,r) for l,r in [p.split('=') for p in data.split('&')]])

    def cancel_recurring(self, cart):
        """Cancel recurring lineitem."""
        pass

    def charge_recurring(self, cart, grace_period=None):
        """Charge a cart's recurring item, if necessary."""
        pass

    def sanitize_clone(self, cart):
        """Nothing to do here..."""
        return cart

    def submit(self, cart, collect_address=False):
        """Submit the cart to the Paypal"""
        # NOTE: This is possible in Paypal, but I don't have time to
        #       implement it right now.
        if cart.lineitems.count() > 0 and cart.recurringlineitems.count() > 0:
            raise Paypal2GatewayError("Recurring and Non-Recurring items can't be mixed.")
        self._update_with_cart_settings(cart)
        params = {"METHOD": "SetExpressCheckout",
                  "CANCELURL": self.settings["CANCEL_URL"],
                  "RETURNURL": self.settings["RETURN_URL"],
                  "NOSHIPPING": "1", # No shipping for now
                  "PAYMENTREQUEST_0_CURRENCYCODE": "USD", # TODO: Make setting
                  "PAYMENTREQUEST_0_ITEMAMT": cart.total.quantize(Decimal(".01")),
                  "PAYMENTREQUEST_0_INVNUM": cart.cart_uuid,
                  "PAYMENTREQUEST_0_MAXAMT": cart.total,
                  "PAYMENTREQUEST_0_NOTIFYURL": self.ipn_url,
                  "PAYMENTREQUEST_0_PAYMENTACTION": "Sale",
                  "PAYMENTREQUEST_0_SELLERPAYPALACCOUNTID": self.settings["EMAIL"],
                }
        if cart.lineitems.count() > 0:
            params["PAYMENTREQUEST_0_AMT"] = cart.total.quantize(Decimal(".01"))
            for i, item in enumerate(cart.lineitems.all()):
                params["L_PAYMENTREQUEST_0_NAME%i"%i] = item.name
                params["L_PAYMENTREQUEST_0_DESC%i"%i] = item.description
                params["L_PAYMENTREQUEST_0_AMT%i"%i] = item.total.quantize(Decimal(".01"))
                params["L_PAYMENTREQUEST_0_NUMBER%i"] = item.sku
        else:
            params["PAYMENTREQUEST_0_AMT"] = cart.total.quantize(Decimal(".01"))
            for i, item in enumerate(cart.recurringlineitems.all()):
                params["L_BILLINGTYPE%i"%i] = "RecurringPayments"
                params["L_BILLINGAGREEMENTDESCRIPTION%i"%i] = item.description
                #params["L_AMT%i"%i] = item.recurring_price.quantize(Decimal(".01"))
                #params["L_PAYMENTREQUEST_0_NAME%i"%i] = item.name
                #params["L_PAYMENTREQUEST_0_DESC%i"%i] = item.description
                params["L_PAYMENTREQUEST_0_AMT%i"%i] = item.total.quantize(Decimal(".01"))
                params["L_PAYMENTREQUEST_0_NUMBER%i"%i] = item.sku
        params["VERSION"] = "64.4"
        params["USER"] = self.settings["USERID"]
        params["PWD"] = self.settings["PASSWORD"]
        params["SIGNATURE"] = self.settings["SIGNATURE"]
        result = self._send_command(params)
        import pdb; pdb.set_trace()
        params = urllib.urlencode({"cmd": "_express-checkout",
                                   "token": result['TOKEN']})
        url = LIVE_REDIRECT if self.settings["LIVE"] else SANDBOX_REDIRECT
        return SubmitResult("url", "%s?%s" % (url, params))
