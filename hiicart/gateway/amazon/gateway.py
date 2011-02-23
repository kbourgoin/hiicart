"""Amazon Payments Gateway"""

import base64
import hashlib
import hmac
import urllib
import urllib2
import urlparse
import xml.etree.cElementTree as ET

from datetime import datetime, tzinfo
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.http import urlencode
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from urllib2 import HTTPError

from hiicart.gateway.amazon import fps, ipn
from hiicart.gateway.amazon.settings import SETTINGS as default_settings
from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult, GatewayError

LIVE_CBUI_URL = "https://authorize.payments.amazon.com/cobranded-ui/actions/start"
TEST_CBUI_URL = "https://authorize.payments-sandbox.amazon.com/cobranded-ui/actions/start"

class AmazonGateway(PaymentGatewayBase):
    """Payment Gateway for Amazon Payments."""

    def __init__(self):
        super(AmazonGateway, self).__init__("amazon", default_settings)
        self._require_settings(["AWS_KEY", "AWS_SECRET"])

    @property
    def _cbui_base_url(self):
        if self.settings["LIVE"]:
            url = mark_safe(LIVE_CBUI_URL)
        else:
            url = mark_safe(TEST_CBUI_URL)
        return url
    
    def _get_cbui_values(self, cart, collect_address=False):
        """Get the key/values to be used in a co-branded UI request."""
        values = {"callerKey" : self.settings["AWS_KEY"],
                  "callerReference" : cart.cart_uuid,
                  "SignatureMethod" : "HmacSHA256",
                  "SignatureVersion" : 2,
                  "version" : "2009-01-09",
                  "returnURL" : self.settings["CBUI_RETURN_URL"],
                  "transactionAmount" : cart.total,
                  "collectShippingAddress": str(collect_address)}
        if cart.recurringlineitems.count() == 0:
            values["pipelineName"] = "SingleUse"
        else:
            if cart.recurringlineitems.count() > 1:
                raise GatewayError("Only one recurring lineitem per cart.")
            recurring = cart.recurringlineitems.all()[0]
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

    def cancel_recurring(self, cart):
        """Cancel recurring lineitem."""
        if cart.recurringlineitems.count() == 0:
            return
        self._update_with_cart_settings(cart)
        item = cart.recurringlineitems.all()[0]
        token = item.payment_token
        response = fps.do_fps("CancelToken", "GET", self.settings, TokenId=token)
        item.is_active = False
        item.save()
        cart.update_state()

    def charge_recurring(self, cart, grace_period=None):
        """
        Charge a cart's recurring item, if necessary.
        NOTE: Currently only one recurring item is supported per cart,
              so charge the first one found.
        """
        self._update_with_cart_settings(cart)
        if not grace_period:
            grace_period = self.settings.get("CHARGE_RECURRING_GRACE_PERIOD", None)
        recurring = cart.recurringlineitems.filter(is_active=True)
        if not recurring or not recurring[0].is_expired(grace_period=grace_period):
            return
        item = recurring[0]
        payments = cart.payments \
                    .filter(state="PAID") \
                    .order_by("-created")
        payment_id= '%s-%i' % (cart.cart_uuid, len(payments)+1)
        result = ipn.AmazonIPN().make_pay_request(cart, item.payment_token,
                                                  payment_id)
        if result != "TokenUsageError" and result != "Pending" and result != "Success":
            # TokenUsageError is if we tried to charge too soon
            item.recurring = False
            item.save()

    def sanitize_clone(self, cart):
        """Nothing to do here..."""
        return cart

    def submit(self, cart, collect_address=False):
        """Submit the cart to Amazon's Co-Branded UI (CBUI)"""
        self._update_with_cart_settings(cart)
        values = self._get_cbui_values(cart, collect_address)
        values["Signature"] = fps.generate_signature("GET", values,
                                                     self._cbui_base_url,
                                                     self.settings)
        url  = "%s?%s" % (self._cbui_base_url, urllib.urlencode(values))
        return SubmitResult("url", url)
