import urllib2

from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.http import urlencode
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from hiicart.gateway.base import IPNBase
from hiicart.gateway.paypal.settings import default_settings
from hiicart.gateway.paypal.errors import PaypalGatewayError
from hiicart.models import HiiCart, Payment

POST_URL = "https://www.paypal.com/cgi-bin/webscr"
POST_TEST_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"

class PaypalIPN(IPNBase):
    """Paypal IPN Handler"""

    def __init__(self):
        super(PaypalIPN, self).__init__("paypal", default_settings)

    @property
    def submit_url(self):
        if self.settings["LIVE"]:
            url = POST_URL
        else:
            url = POST_TEST_URL
        return mark_safe(url)

    def _find_cart(self, data):
        # invoice may have a suffix due to retries
        invoice = data["invoice"] if "invoice" in data else data["item_number"]
        if not invoice:
            self.log.error("No invoice # in data, aborting IPN")
            return None
        try:
            return HiiCart.objects.get(_cart_uuid=invoice[:36])
        except HiiCart.DoesNotExist:
            return None        

    def accept_payment(self, data):
        """Accept a successful Paypal payment"""
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
            payment.notes.create(text="Comment via Paypal IPN: \n%s" % data["note"])
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

    def activate_subscription(self, data):
        """Send signal that a subscription has been activated."""
        cart = self._find_cart(data)
        if not cart:
            self.log.warn("Unable to find purchase for IPN.")
            return
        sku = data.get("item_number", None)
        item = cart.recurringlineitems.get(sku=sku) if sku else None 
        if item:
            item.is_active = True
            item.save()
            cart.update_state()

    def cancel_subscription(self, data):
        """Send signal that a subscription has been cancelled."""
        cart = self._find_cart(data)
        if not cart:
            self.log.warn("Unable to find purchase for IPN.")
            return
        sku = data.get("item_number", None)
        item = cart.recurringlineitems.get(sku=sku) if sku else None 
        if item:
            item.is_active = False 
            item.save()
            cart.update_state()

    def confirm_ipn_data(self, raw_data):
        """Confirm IPN data using string raw post data.

        Overcomes issues with unicode and urlencode.
        """
        raw_data += "&cmd=_notify-validate"
        req = urllib2.Request(self.submit_url)
        req.add_header("Content-type", "application/x-www-form-urlencoded")
        result = urllib2.urlopen(req, raw_data)
        ret = result.read()
        if ret == "VERIFIED":
            return True
        else:
            return False
