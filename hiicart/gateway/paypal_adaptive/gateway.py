"""Paypal Adaptive Payments Gateway"""

import urllib

from decimal import Decimal
from django.core.urlresolvers import reverse

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult, GatewayError
from hiicart.gateway.paypal_adaptive import api
from hiicart.gateway.paypal_adaptive.settings import SETTINGS as default_settings

POST_URL = "https://www.paypal.com/cgi-bin/webscr"
POST_TEST_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"

class PaypalAPGateway(PaymentGatewayBase):
    """Payment Gateway for Paypal Adaptive Payments."""

    def __init__(self, cart):
        super(PaypalAPGateway, self).__init__("paypal_adaptive", cart, default_settings)
        self._require_settings(["APP_ID", "PASSWORD", "SIGNATURE", "USERID"])

    @property
    def ipn_url(self):
        if "IPN_URL" not in self.settings:
            if "BASE_URL" not in self.settings:
                raise GatewayError(
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

    def _is_valid(self):
        """Return True if gateway is valid."""
        # TODO: Query Paypal to validate credentials
        return True

    def cancel_recurring(self):
        """Cancel recurring lineitem."""
        raise GatewayError("Adaptive Payments doesn't support recurring payments.")

    def charge_recurring(self, grace_period=None):
        """Charge a cart's recurring item, if necessary."""
        raise GatewayError("Adaptive Payments doesn't support recurring payments.")

    def sanitize_clone(self):
        """Nothing to do here..."""
        return self.cart

    def submit(self, collect_address=False, cart_settings_kwargs=None):
        """Submit the cart to the Paypal Adaptive Payments API"""
        self._update_with_cart_settings(self.cart, cart_settings_kwargs)
        if len(self.cart.recurring_lineitems) > 0:
            raise GatewayError("Adaptive Payments doesn't support recurring payments.")
        params = {"actionType": "PAY",
                  "currencyCode": "USD",
                  "feesPayer": "EACHRECEIVER",
                  "cancelUrl": self.settings["CANCEL_URL"],
                  "returnUrl": self.settings["RETURN_URL"],
                  "ipnNotificationUrl": self.ipn_url,
                  "trackingId": self.cart.cart_uuid,
                }
        for i, r in enumerate(self.settings["RECEIVERS"]):
            params["receiverList.receiver(%i).email" % i] = r[0]
            params["receiverList.receiver(%i).amount" % i] = r[1].quantize(Decimal(".01"))
            params["receiverList.receiver(%i).primary" % i] = str(r[2]).lower()
        result = api._send_command(self.settings, "Pay", params)
        params = urllib.urlencode({"cmd": "_ap-payment",
                                   "paykey": result['payKey']})
        return SubmitResult("url", "%s?%s" % (self.submit_url, params))
