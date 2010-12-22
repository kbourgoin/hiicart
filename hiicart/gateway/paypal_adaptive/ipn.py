import re
import urllib
import urllib2
import urlparse
import xml.etree.cElementTree as ET

from datetime import datetime, tzinfo
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.datastructures import SortedDict
from urllib2 import HTTPError

from hiicart.gateway.paypal_adaptive.errors import PaypalAPGatewayError
from hiicart.gateway.paypal_adaptive.settings import default_settings
from hiicart.gateway.base import IPNBase
from hiicart.models import HiiCart, Payment

# Payment State translation between Adaptive API and HiiCart
_adaptive_states = {
        "Completed": "PAID",
        "Created": "PENDING",
        "Processing": "PENDING",
    }


class PaypalAPIPN(IPNBase):
    """Payment Gateway for Paypal Adaptive Payments."""

    def __init__(self):
        super(PaypalAPIPN, self).__init__(
                "paypal_adaptive", default_settings)

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

    def accept_adaptive_payment(self, data):
        """Accept a payment IPN coming through the Adaptive API.

        Paypal sends out two kind of IPNs when using Adaptive. The
        payment initiator (HiiCart) will get an Adaptive-specific IPN
        relating to the overall state of the payment.  HiiCart may also
        receive normal Paypal IPNs if the user has their IPN url pointing
        here."""
        self.log.debug("IPN for cart %s received" % data["tracking_id"])
        cart = HiiCart.objects.get(_cart_uuid=data["tracking_id"])
        for i in range(6):
            key_base = "transaction[%i]." % i
            if not any([k.startswith(key_base) for k in data.keys()]):
                break
            p = Payment.objects.filter(transaction_id=data[key_base + "id"])
            if len(p) == 0:
                p = Payment(cart=cart, gateway=cart.gateway,
                            transaction_id=data[key_base + "id"])
            else:
                p = p[0]
            amount = re.sub("[^0-9.]", "", data[key_base + "amount"])
            p.amount = Decimal(amount)
            p.state = _adaptive_states[data[key_base + "status"]]
            p.save() # Need .id if creating new payment
            p.notes.create(text="Payment receiver: %s" % data[key_base + "receiver"])
        if "memo" in data:
            cart.notes.create(text="IPN Memo: %s" % data["memo"])
        cart.update_state()

    def accept_payment(self, data):
        """Accept a normal PayPal payment IPN.

        Paypal sends out two kind of IPNs when using Adaptive. The
        payment initiator (HiiCart) will get an Adaptive-specific IPN
        relating to the overall state of the payment.  HiiCart may also
        receive normal Paypal IPNs if the user has their IPN url pointing
        here."""
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

        Overcomes issues with unicode and urlencode.
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
