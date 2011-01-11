import re
import httplib2
import urllib
import urllib2
import urlparse

from datetime import datetime, tzinfo
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.datastructures import SortedDict
from urllib import unquote
from urllib2 import HTTPError

from hiicart.gateway.base import IPNBase, GatewayError
from hiicart.gateway.paypal2.settings import SETTINGS as default_settings
from hiicart.models import HiiCart, Payment

class Paypal2IPN(IPNBase):
    """Payment Gateway for Paypal Adaptive Payments."""

    def __init__(self):
        super(Paypal2IPN, self).__init__("paypal2", default_settings)

    def _find_cart(self, data):
        # invoice may have a suffix due to retries
        invoice = data["invoice"] if "invoice" in data else data["item_number"]
        if not invoice:
            self.log.warn("No invoice # in data, aborting IPN")
            return None
        try:
            return HiiCart.objects.get(_cart_uuid=invoice[:36])
        except HiiCart.DoesNotExist:
            return None        

    def accept_payment(self, data):
        """Accept a PayPal payment IPN."""
        # TODO: Should this simple mirror/reuse what's in gateway.paypal?
        transaction_id = data["txn_id"]
        self.log.debug("IPN for transaction #%s received" % transaction_id)
        if Payment.objects.filter(transaction_id=transaction_id).count() > 0:
            self.log.warn("IPN #%s, already processed", transaction_id)
            return
        cart = self._find_cart(data)
        if not cart:
            self.log.warn("Unable to find purchase for IPN.")
            return
        payment = self._create_payment(cart, data["mc_gross"],
                                       transaction_id, "PAID")
        if data.get("note", False):
            payment.notes.create(text="Comment via IPN: \n%s" % data["note"])
        # Fill in billing information. Consider any already in HiiCart correct
        cart.email = cart.email or data.get("payer_email", "")
        cart.first_name = cart.first_name or data.get("first_name", "")
        cart.last_name = cart.last_name or data.get("last_name", "")
        street = data.get("address_street", "")
        cart.bill_street1 = cart.bill_street1 or street.split("\r\n")[0]
        if street.count("\r\n") > 0:
            cart.bill_street2 = cart.bill_street2 or street.split("\r\n")[1]
        cart.bill_city = cart.bill_city or data.get("address_city", "")
        cart.bill_state = cart.bill_state or data.get("address_state", "")
        cart.bill_postal_code = cart.bill_postal_code or data.get("address_zip", "")
        cart.bill_country = cart.bill_country or data.get("address_country_code", "")
        cart.update_state()
        cart.save()

    def confirm_ipn_data(self, raw_data):
        """Confirm IPN data using string raw post data.

        Using the raw data overcomes issues with unicode and urlencode.
        """
        if self.settings["LIVE"]:
            submit_url = "https://www.paypal.com/cgi-bin/webscr"
        else:
            submit_url = "https://www.sandbox.paypal.com/cgi-bin/webscr"
        raw_data += "&cmd=_notify-validate"
        req = urllib2.Request(submit_url)
        req.add_header("Content-type", "application/x-www-form-urlencoded")
        result = urllib2.urlopen(req, raw_data).read()
        return urllib2.urlopen(req, raw_data).read() == "VERIFIED"

