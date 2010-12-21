"""Paypal Adaptive Payments Gateway"""

import urllib

from decimal import Decimal
from django.core.urlresolvers import reverse

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult
from hiicart.gateway.paypal_adaptive import api
from hiicart.gateway.paypal_adaptive.errors import PaypalAdaptivePaymentsGatewayError
from hiicart.gateway.paypal_adaptive.settings import default_settings

POST_URL = "https://www.paypal.com/cgi-bin/webscr"
POST_TEST_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"

class PaypalAdaptivePaymentsGateway(PaymentGatewayBase):
    """Payment Gateway for Paypal Adaptive Payments."""

    def __init__(self):
        super(PaypalAdaptivePaymentsGateway, self).__init__(
                "paypal_adaptive", default_settings)

    @property
    def ipn_url(self):
        if "IPN_URL" not in self.settings:
            if "BASE_URL" not in self.settings:
                raise PaypalAdaptivePaymentsGatewayError(
                        "Either IPN_URL or BASE_URL is required.")
            # Import here to avoid circular import
            from hiicart.gateway.paypal_adaptive.views import ipn
            return "%s%s" % (self.settings["BASE_URL"], reverse(ipn))
        else:
            return self.settings["IPN_URL"]

    @property
    def submit_url(self):
        if self.settings["LIVE"]:
            url = POST_URL
        else:
            url = POST_TEST_URL
        return url

    def cancel_recurring(self, cart):
        """Cancel recurring lineitem."""
        pass

    def charge_recurring(self, cart, grace_period=None):
        """
        Charge a cart's recurring item, if necessary.
        NOTE: Currently only one recurring item is supported per cart,
              so charge the first one found.
        """
        pass

    def sanitize_clone(self, cart):
        """Nothing to do here..."""
        return cart

    def submit(self, cart, collect_address=False):
        """Submit the cart to the Paypal Adaptive Payments API"""
        self._update_with_cart_settings(cart)
        params = {"actionType": "PAY",
                  "currencyCode": "USD",
                  "memo": "test payment",
                  "feesPayer": "EACHRECEIVER",
#                  "reverseAllParallelPaymentsOnError": "true",
                  "cancelUrl": self.settings["CANCEL_URL"],
                  "returnUrl": self.settings["RETURN_URL"],
                  "ipnNotificationUrl": self.ipn_url,
                  "trackingId": cart.cart_uuid,
                }
        for i, r in enumerate(self.settings["RECEIVERS"]):
            params["receiverList.receiver(%i).email" % i] = r[0]
            params["receiverList.receiver(%i).amount" % i] = r[1].quantize(Decimal(".01"))
            params["receiverList.receiver(%i).primary" % i] = str(r[2]).lower()
        result = api._send_command(self.settings, "Pay", params)
        params = urllib.urlencode({"cmd": "_ap-payment",
                                   "paykey": result['payKey']})
        return SubmitResult("url", "%s?%s" % (self.submit_url, params))
