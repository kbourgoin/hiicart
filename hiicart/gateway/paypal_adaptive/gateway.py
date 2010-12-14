"""Paypal Adaptive Payments Gateway"""

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

from hiicart.gateway.paypal_adaptive import fps, ipn
from hiicart.gateway.paypal_adaptive.errors import PaypalAdaptivePaymentsGatewayError
from hiicart.gateway.paypal_adaptive.settings import default_settings
from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult

LIVE_ENDPOINT = "https://svcs.paypal.com/AdaptivePayments/API_operation"
SANDBOX_ENDPOINT = "https://svcs.paypal.com/AdaptivePayments/API_operation"

class PaypalAdaptivePaymentsGateway(PaymentGatewayBase):
    """Payment Gateway for Paypal Adaptive Payments."""

    def __init__(self):
        super(PaypalAdaptivePaymentsGateway, self).__init__(
                "paypal_adaptive", default_settings)

    @property
    def _endpoint_url(self):
        if self.settings["LIVE"]:
            return LIVE_ENDPOINT
        else:
            return SANDBOX_ENDPOINT
    
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
        pass
