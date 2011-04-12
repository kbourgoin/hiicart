"""Amazon Payments Gateway"""

import urllib
from datetime import datetime
from decimal import Decimal
from django.utils.safestring import mark_safe
from hiicart.gateway.amazon import fps, ipn
from hiicart.gateway.amazon.settings import SETTINGS as default_settings
from hiicart.gateway.base import PaymentGatewayBase, SubmitResult, GatewayError


LIVE_CBUI_URL = "https://authorize.payments.amazon.com/cobranded-ui/actions/start"
TEST_CBUI_URL = "https://authorize.payments-sandbox.amazon.com/cobranded-ui/actions/start"


class AmazonGateway(PaymentGatewayBase):
    """Payment Gateway for Amazon Payments."""

    def __init__(self, cart):
        super(AmazonGateway, self).__init__("amazon", cart, default_settings)
        self._require_settings(["AWS_KEY", "AWS_SECRET"])

    @property
    def _cbui_base_url(self):
        if self.settings["LIVE"]:
            url = mark_safe(LIVE_CBUI_URL)
        else:
            url = mark_safe(TEST_CBUI_URL)
        return url

    def _get_cbui_values(self, collect_address=False):
        """Get the key/values to be used in a co-branded UI request."""
        values = {"callerKey" : self.settings["AWS_KEY"],
                  "CallerReference" : self.cart.cart_uuid,
                  "SignatureMethod" : "HmacSHA256",
                  "SignatureVersion" : 2,
                  "version" : "2009-01-09",
                  "returnURL" : self.settings["CBUI_RETURN_URL"],
                  "transactionAmount" : self.cart.total,
                  "collectShippingAddress": str(collect_address)}
        if len(self.cart.recurring_lineitems) == 0:
            values["pipelineName"] = "SingleUse"
        else:
            if len(self.cart.recurring_lineitems) > 1:
                raise GatewayError("Only one recurring lineitem per cart.")
            recurring = self.cart.recurring_lineitems[0]
            values["pipelineName"] = "Recurring"
            values["recurringPeriod"] = "%s %s" % (
                    recurring.duration, recurring.duration_unit)
            if recurring.recurring_start and recurring.recurring_start > datetime.now():
                values["validityStart"] = recurring.recurring_start.strftime('%s')
        # Optional Fields
        if self.settings["CBUI_WEBSITE_DESC"]:
            values["websiteDescription"] = self.settings["CBUI_WEBSITE_DESC"]
        methods = self._get_payment_methods()
        if methods:
            values["paymentMethod"] = methods
        return values

    def _get_payment_methods(self):
        methods = []
        if self.settings["ACCEPT_CC"]:
            methods.append("CC")
        if self.settings["ACCEPT_ACH"]:
            methods.append("ACH")
        if self.settings["ACCEPT_ABT"]:
            methods.append("ABT")
        return ",".join(methods)

    def _is_valid(self):
        """Return True if gateway is valid."""
        #TODO: Query Amazon to validate credentials
        return True

    def cancel_recurring(self):
        """Cancel recurring lineitem."""
        if len(self.cart.recurring_lineitems) == 0:
            return
        item = self.cart.recurring_lineitems[0]
        token = item.payment_token
        response = fps.do_fps("CancelToken", "GET", self.settings, TokenId=token)
        item.is_active = False
        item.save()
        self.cart.update_state()

    def charge_recurring(self, grace_period=None):
        """
        Charge a cart's recurring item, if necessary.
        NOTE: Currently only one recurring item is supported per cart,
              so charge the first one found.
        """
        if not grace_period:
            grace_period = self.settings.get("CHARGE_RECURRING_GRACE_PERIOD", None)
        recurring = [li for li in self.cart.recurring_lineitems if li.is_active]
        if not recurring or not recurring[0].is_expired(grace_period=grace_period):
            return
        item = recurring[0]
        payments = self.cart.payments \
                    .filter(state="PAID") \
                    .order_by("-created")
        payment_id= '%s-%i' % (self.cart.cart_uuid, len(payments)+1)
        result = ipn.AmazonIPN(self.cart).make_pay_request(item.payment_token, payment_id)
        if result != "TokenUsageError" and result != "Pending" and result != "Success":
            # TokenUsageError is if we tried to charge too soon
            item.recurring = False
            item.save()

    def sanitize_clone(self):
        """Nothing to do here..."""
        return self.cart

    def submit(self, collect_address=False, cart_settings_kwargs=None):
        """Submit the cart to Amazon's Co-Branded UI (CBUI)"""
        self._update_with_cart_settings(cart_settings_kwargs)
        values = self._get_cbui_values(collect_address)
        values["Signature"] = fps.generate_signature("GET", values,
                                                     self._cbui_base_url,
                                                     self.settings)
        url  = "%s?%s" % (self._cbui_base_url, urllib.urlencode(values))
        return SubmitResult("url", url)
