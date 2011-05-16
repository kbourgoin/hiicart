import urllib2
from django.utils.safestring import mark_safe
from hiicart.gateway.base import IPNBase
from hiicart.gateway.paypal.settings import SETTINGS as default_settings


POST_URL = "https://www.paypal.com/cgi-bin/webscr"
POST_TEST_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"


class PaypalIPN(IPNBase):
    """Paypal IPN Handler"""

    def __init__(self, cart):
        super(PaypalIPN, self).__init__("paypal", cart, default_settings)

    @property
    def submit_url(self):
        if self.settings["LIVE"]:
            url = POST_URL
        else:
            url = POST_TEST_URL
        return mark_safe(url)

    def accept_payment(self, data):
        """Accept a successful Paypal payment"""
        transaction_id = data["txn_id"]
        self.log.debug("IPN for transaction #%s received" % transaction_id)
        if self.cart.payment_class.objects.filter(transaction_id=transaction_id).count() > 0:
            self.log.warn("IPN #%s, already processed", transaction_id)
            return
        if not self.cart:
            self.log.warn("Unable to find purchase for IPN.")
            return
        # Fill in billing information. Consider any already in HiiCart correct
        self.cart.bill_email = self.cart.bill_email or data.get("payer_email", "")
        self.cart.ship_email = self.cart.ship_email or self.cart.bill_email
        self.cart.bill_first_name = self.cart.bill_first_name or data.get("first_name", "")
        self.cart.ship_first_name = self.cart.ship_first_name or self.cart.bill_first_name
        self.cart.bill_last_name = self.cart.bill_last_name or data.get("last_name", "")
        self.cart.ship_last_name = self.cart.ship_last_name or self.cart.bill_last_name
        street = data.get("address_street", "")
        self.cart.bill_street1 = self.cart.bill_street1 or street.split("\r\n")[0]
        self.cart.ship_street1 = self.cart.ship_street1 or street.split("\r\n")[0]
        if street.count("\r\n") > 0:
            self.cart.bill_street2 = self.cart.bill_street2 or street.split("\r\n")[1]
            self.cart.ship_street2 = self.cart.ship_street2 or self.cart.bill_street2
        self.cart.bill_city = self.cart.bill_city or data.get("address_city", "")
        self.cart.ship_city = self.cart.ship_city or self.cart.bill_city
        self.cart.bill_state = self.cart.bill_state or data.get("address_state", "")
        self.cart.ship_state = self.cart.ship_state or self.cart.bill_state
        self.cart.bill_postal_code = self.cart.bill_postal_code or data.get("address_zip", "")
        self.cart.ship_postal_code = self.cart.ship_postal_code or self.cart.bill_postal_code
        self.cart.bill_country = self.cart.bill_country or data.get("address_country_code", "")
        self.cart.ship_country = self.cart.ship_country or self.cart.bill_country
        self.cart.save()
        payment = self._create_payment(data["mc_gross"], transaction_id, "PENDING")
        payment.state = "PAID" # Ensure proper state transitions
        payment.save()
        if data.get("note", False):
            payment.notes.create(text="Comment via Paypal IPN: \n%s" % data["note"])
        self.cart.update_state()
        self.cart.save()

    def activate_subscription(self, data):
        """Send signal that a subscription has been activated."""
        if not self.cart:
            self.log.warn("Unable to find purchase for IPN.")
            return
        sku = data.get("item_number", None)
        if sku:
            recurring_by_sku = dict([(li.sku, li) for li in self.cart.recurring_lineitems])
            item = recurring_by_sku.get(sku)
        else:
            item = None
        if item:
            item.is_active = True
            item.save()
            self.cart.update_state()
            self.cart.save()

    def cancel_subscription(self, data):
        """Send signal that a subscription has been cancelled."""
        if not self.cart:
            self.log.warn("Unable to find purchase for IPN.")
            return
        sku = data.get("item_number", None)
        recurring_by_sku = dict([(li.sku, li) for li in self.cart.recurring_lineitems])
        item = recurring_by_sku.get(sku)
        if item:
            item.is_active = False
            item.save()
            self.cart.update_state()
            self.cart.save()

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
