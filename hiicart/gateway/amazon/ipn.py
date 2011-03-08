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

from hiicart.gateway.amazon import fps
from hiicart.gateway.amazon.settings import SETTINGS as default_settings
from hiicart.gateway.base import IPNBase
from hiicart.models import HiiCart, Payment

_FPS_NS = "{http://fps.amazonaws.com/doc/2008-09-17/}"

class AmazonIPN(IPNBase):
    """Payment Gateway for Amazon Payments."""

    def __init__(self):
        super(AmazonIPN, self).__init__("amazon", default_settings)

    def _process_error(self, response):
        """Process error xml into (code, message, requestId)."""
        xml = ET.XML(response)
        code = xml.find(".//Code")
        message = xml.find(".//Message")
        request_id = xml.find(".//RequestID")
        if code is not None and message is not None and request_id is not None:
            return (code.text, message.text, request_id.text)
        return None

    def accept_payment(self, cart, data):
        """Record payment received from IPN."""
        total = None
        if "transactionAmount" in data and data["transactionAmount"].startswith("USD "):
            total = Decimal(data["transactionAmount"][4:])
        if data["transactionStatus"] == "PENDING":
            transaction_id = data["transactionId"]
            pending = cart.payments.filter(transaction_id=transaction_id)
            if not pending: # Could already be created in make_pay_request
                self._create_payment(cart, total, transaction_id, "PENDING")
        elif data["transactionStatus"] == "SUCCESS":
            # Was this a pending payment?
            transaction_id = data["transactionId"]
            pending = cart.payments.filter(transaction_id=transaction_id, state="PENDING")
            if pending:
                pending[0].state = "PAID"
                pending[0].save()
            elif cart.payments.filter(transaction_id=transaction_id).count() == 0: # No duplicate payments
                self._create_payment(cart, total, transaction_id, "PAID")
            cart.update_state()
            self.begin_recurring(cart)
        elif data["transactionStatus"] == "CANCELLED":
            message = "Purchase %i (txn:%s) was cancelled with message '%s'" % (
                      cart.id, data['transactionId'], data['statusMessage'])
            self.log.warn(message)
            transaction_id = data["transactionId"]
            cancelled = cart.payments.filter(transaction_id=transaction_id)
            for p in cancelled:
                p.state = "CANCELLED"
                p.notes.create(text=message)
                p.save()
            cart.update_state()
        elif data["transactionStatus"] == "FAILURE":
            self.log.warn("Purchase %i (txn:%s) failed with message '%s'" % (
                cart.id, data['transactionId'], data['statusMessage']))
            cart.update_state()

    def begin_recurring(self, cart):
        """Save token and mark recurring item as active."""
        if len(cart.recurring_lineitems) == 0:
            return
        for ri in cart.recurring_lineitems:
            ri.is_active = True
            ri.save()
        cart.update_state()

    def end_recurring(self, cart, token):
        """Mark a recurring item as inactive."""
        if len(cart.recurring_lineitems) == 0:
            return
        for ri in cart.recurring_lineitems:
            ri.is_active = False
            ri.save()
        cart.update_state()

    def make_pay_request(self, cart, token, caller_reference=None):
        """
        Make a Pay request for the purchase with the given token.
        Return status received from Amazon.
        """
        self._update_with_store_settings(cart)
        if caller_reference is None:
            caller_reference = cart.cart_uuid
        response = fps.do_fps("Pay", "GET", self.settings,
                   **{"CallerReference" : caller_reference,
                      "SenderTokenId" : token,
                      "TransactionAmount.CurrencyCode" : "USD",
                      "TransactionAmount.Value" : cart.total})
        xml = ET.XML(response)
        status = xml.find(".//%sTransactionStatus" % _FPS_NS)
        if status is None:
            error = self._process_error(response)
            if not error:
                msg = "Pay request failed for purchase '%s' with response: %s" % (
                            cart, response)
            else:
                msg = "Pay request failed for purchase '%s' with code/message: '%s' '%s' (request id: '%s')" % (
                            cart, error[0], error[1], error[2])
            self.log.warn(msg)
            cart.notes.create(text=msg)
            # An error code, maybe?
            code = xml.find(".//Code")
            if code is not None:
                return code.text
            return None
        else:
            # This work for pending payments?
            transaction_id = xml.find(".//%sTransactionId" % _FPS_NS).text
            if status.text == "Pending":
                self._create_payment(cart, cart.total, transaction_id, "PENDING")
            elif status.text == "Success":
                pending = cart.payments.filter(transaction_id=transaction_id,
                                               state="PENDING")
                if pending:
                    pending[0].state = "PAID"
                    pending[0].save()
                else:
                    self._create_payment(cart, cart.total, transaction_id, "PAID")
                self.begin_recurring(cart)
            else: # Cancelled or Failure
                msg = "Pay request for purchase '%s' returned status '%s'. \nFull response: %s" % (
                            cart, response)
                self.log.warn(msg)
                cart.notes.create(text=msg)
            cart.update_state()
            return status.text

    def save_recurring_token(self, cart, token):
        """Save recurring use token for future use."""
        if len(cart.recurring_lineitems) == 0:
            return
        ri = cart.recurring_lineitems[0]
        ri.payment_token = token
        ri.save()

    def verify_signature(self, raw_data, http_method, endpoint_uri, cart):
        self._update_with_store_settings(cart)
        response = fps.do_fps("VerifySignature", http_method, self.settings,
                              UrlEndPoint=endpoint_uri,
                              HttpParameters=raw_data)
        xml = ET.XML(response)
        el = xml.find(".//{http://fps.amazonaws.com/doc/2008-09-17/}VerificationStatus")
        return el is not None and el.text == "Success"
