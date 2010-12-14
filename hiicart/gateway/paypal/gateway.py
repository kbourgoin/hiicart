import os
import urllib2

from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.http import urlencode
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult
from hiicart.gateway.paypal.errors import PaypalGatewayError
from hiicart.gateway.paypal.settings import default_settings

PAYMENT_CMD = {
    "BUY_NOW" : "_xclick",
    "CART" : "_cart",
    "SUBSCRIPTION" : "_xclick-subscriptions",
    "UNSUBSCRIBE" : "_subscr-find"
    }
NO_SHIPPING = {
    "NO" : "1",
    "YES" : "0"
    }
NO_NOTE = {
    "NO" : "1",
    "YES" : "0"
    }
RECURRING_PAYMENT = {
    "YES" : "1",
    "NO" : "0"
    }

POST_URL = "https://www.paypal.com/cgi-bin/webscr"
POST_TEST_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"

class PaypalGateway(PaymentGatewayBase):
    """Paypal payment processor"""

    def __init__(self):
        super(PaypalGateway, self).__init__("paypal", default_settings)
        self._require_settings(["BUSINESS"])
        if self.settings["ENCRYPT"]:
            self._require_settings(["PRIVATE_KEY", "PUBLIC_KEY", "PUBLIC_CERT_ID"])
            self.localprikey = self.settings[ "PRIVATE_KEY"]
            self.localpubkey = self.settings["PUBLIC_KEY"]
            self.paypalpubkey = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                "keys/paypal.%s.pem" % ("live" if self.settings["LIVE"] else "sandbox")))
            self._require_files([self.paypalpubkey, self.localpubkey, self.localprikey])
            try:
                import M2Crypto
            except ImportError:
                raise PaypalGatewayError("paypal_gateway: You must install M2Crypto to use an encrypted PayPal form.")

    @property
    def submit_url(self):
        if self.settings["LIVE"]:
            url = POST_URL
        else:
            url = POST_TEST_URL
        return mark_safe(url)

    @property
    def submit_button_url(self, cart):
        if cart.recurringlineitems.count() > 0:
            url = self.settings["SUBSCRIBE_BUTTON_URL"]
        else:
            url = self.settings["BUY_BUTTON_URL"]
        return mark_safe(url)

    def _encrypt_data(self, data):
        """
        Encrypt the form data.  

        Refer to http://sandbox.rulemaker.net/ngps/m2/howto.smime.html
        """
        # Don't import at top because these are only required if user wants encryption
        from M2Crypto import BIO, SMIME, X509
        certid = self.settings["PUBLIC_CERT_ID"]
        # Assemble form data and encode in utf-8
        raw = ["cert_id=%s" % certid]
        raw.extend([u"%s=%s" % (key, val) for key, val in data.items() if val])
        raw = "\n".join(raw)
        raw = raw.encode("utf-8")        
        # make an smime object
        s = SMIME.SMIME()
        # load our public and private keys
        s.load_key_bio(BIO.openfile(self.localprikey),
                       BIO.openfile(self.localpubkey))
        # put the data in the buffer
        buf = BIO.MemoryBuffer(raw)
        # sign the text
        p7 = s.sign(buf, flags=SMIME.PKCS7_BINARY)
        # Load target cert to encrypt to.
        x509 = X509.load_cert_bio(BIO.openfile(self.paypalpubkey))
        sk = X509.X509_Stack()
        sk.push(x509)
        s.set_x509_stack(sk)
        # Set cipher: 3-key triple-DES in CBC mode.
        s.set_cipher(SMIME.Cipher("des_ede3_cbc"))
        # save data to buffer
        tmp = BIO.MemoryBuffer()
        p7.write_der(tmp)
        # encrypt
        p7 = s.encrypt(tmp, flags=SMIME.PKCS7_BINARY)
        out = BIO.MemoryBuffer()
        # write into a new buffer
        p7.write(out)
        return out.read()
        
    def _get_form_data(self, cart):
        """Creates a list of key,val to be sumbitted to PayPal."""
        account = self.settings["BUSINESS"]
        submit = SortedDict()        
        submit["business"] = account
        submit["currency_code"] = self.settings["CURRENCY_CODE"]
        submit["notify_url"] = self.settings["IPN_URL"]
        if self.settings["RETURN_ADDRESS"]:
            submit["return"] = self.settings["RETURN_ADDRESS"]
        #TODO: eventually need to work out the terrible PayPal shipping stuff
        #      for now, we are saying "no shipping" and adding all shipping as
        #      a handling charge.
        submit["no_shipping"] = NO_SHIPPING["YES"]
        submit["handling_cart"] = cart.shipping
        submit["tax_cart"] = cart.tax
        # Locale
        submit["lc"] = self.settings["LOCALE"]
        submit["invoice"] = cart.cart_uuid
        if cart.recurringlineitems.count() > 1:
            self.log.error("Cannot have more than one subscription in one order for paypal.  Only processing the first one for %s", cart)
            return
        if cart.recurringlineitems.count() > 0:
            item = cart.recurringlineitems.all()[0]
            submit["src"] = "1"
            submit["cmd"] = PAYMENT_CMD["SUBSCRIPTION"]
            submit["item_name"] = item.name
            submit["item_number"] = item.sku
            submit["no_note"] = NO_NOTE["YES"]
            submit["bn"] = "PP-SubscriptionsBF"
            if item.trial and item.recurring_start:
                raise PaypalGatewayError("PayPal can't have trial and delayed start")
            if item.recurring_start:
                delay = item.recurring_start - datetime.now()
                delay += timedelta(days=1) # Round up 1 day to PP shows right start
                if delay.days > 90:
                    raise PaypalGatewayError("PayPal doesn't support a delayed start of more than 90 days.")
                # Delayed subscription starts
                submit["a1"] = "0"
                submit["p1"] = delay.days
                submit["t1"] = "D"
            elif item.trial:   
                # initial trial
                submit["a1"] = item.trial_price
                submit["p1"] = item.trial_length
                submit["t1"] = item.duration_unit
                if recur.recurdetails.trial_times > 1:
                    submit["a2"] = item.trial_price
                    submit["p2"] = item.trial_length
                    submit["t2"] = item.duration_unit
            else:
                # Messes up trial periods, so only use if no trial/delay
                submit["modify"] = "1"  # new or modify subscription
            # subscription price
            submit["a3"] = item.recurring_price
            submit["p3"] = item.duration
            submit["t3"] = item.duration_unit
            submit["srt"] = item.recurring_times
            if self.settings["REATTEMPT"]:
                reattempt = "1"
            else:
                reattempt = "0"
            submit["sra"] = reattempt
        else:
            submit["cmd"] = PAYMENT_CMD["CART"]
            submit["upload"] = "1"
            ix = 1
            for item in cart.lineitems.all():
                submit["item_name_%i" % ix] = item.name
                submit["amount_%i" % ix] = item.unit_price.quantize(Decimal(".01"))
                submit["quantity_%i" % ix] = item.quantity
                ix += 1
        if cart.bill_street1:
            submit["first_name"] = cart.first_name
            submit["last_name"] = cart.last_name
            submit["address1"] = cart.bill_street1
            submit["address2"] = cart.bill_street2
            submit["city"] = cart.bill_city
            submit["country"] = cart.bill_country
            submit["zip"] = cart.bill_postal_code
            submit["email"] = cart.email
            submit["address_override"] = "0"
            # only U.S. abbreviations may be used here
            if cart.bill_country.lower() == "us" and len(cart.bill_state) == 2:
                submit["state"] = cart.bill_state
        return submit

    def cancel_recurring(self, cart):
        """Cancel recurring items with gateway. Returns a CancelResult."""
        self._update_with_cart_settings(cart)
        alias = self.settings["BUSINESS"]
        button_url = self.settings["UNSUBSCRIBE_BUTTON_URL"]
        url = "%s?cmd=%s&alias=%s" % (self.submit_url, 
                                      PAYMENT_CMD["UNSUBSCRIBE"],
                                      self.settings["BUSINESS"])
        return CancelResult("url", url=url)

    def charge_recurring(self, cart, grace_period=None):
        """This Paypal API doesn't support manually charging subscriptions."""
        pass

    def sanitize_clone(self, cart):
        """Nothing to fix here."""
        pass

    def submit(self, cart, collect_address=False):
        """Submit a cart to the gateway. Returns a SubmitResult."""
        self._update_with_cart_settings(cart)
        data = self._get_form_data(cart)
        if self.settings["ENCRYPT"]:
            data = {"encrypted": self._encrypt_data(data)}
        return SubmitResult("form", form_data={"action": self.submit_url,
                                               "fields": data})
