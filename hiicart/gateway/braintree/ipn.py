import braintree
from datetime import datetime
from decimal import Decimal
from hiicart.gateway.base import IPNBase
from hiicart.gateway.braintree.settings import SETTINGS as default_settings
from hiicart.models import CART_TYPES


class BraintreeIPN(IPNBase):
    """Braintree IPN Handler."""

    def __init__(self, cart):
        super(BraintreeIPN, self).__init__("braintree", cart, default_settings)
        self._require_settings(["MERCHANT_ID", "MERCHANT_KEY", "MERCHANT_PRIVATE_KEY"])

    @staticmethod
    def _find_payment(data):
        """Find a payment based on the google id"""
        transaction_id = data["google-order-number"]
        for Cart in CART_TYPES:
            try:
                return Cart.payment_class.objects.select_related('cart').get(transaction_id=transaction_id)
            except:
                pass

    def _record_payment(self, amount, id, state="PENDING"):
        """Record a payment from the IPN data."""
        if not self.cart:
            return
        payment = self._create_payment(amount, id, state)
        payment.save()
        return payment

    def create_payment(self, transaction):
        """Create a new payment record."""
        if not self.cart:
            return
        if transaction.status == "settled" or transaction.status == "authorized":
            state = "PAID"
        elif transaction.status == "authorizing" or transaction.status == "submitted_for_settlement":
            state = "PENDING"
        else:
            return False
        payment = self._record_payment(transaction.amount, transaction.id, state)
        return True

    def new_order(self, transaction):
        """Save a new order."""
        if not self.cart:
            return
        self.cart.ship_first_name = transaction.shipping["first_name"]
        self.cart.ship_last_name = transaction.shipping["last_name"]
        self.cart.ship_street1 = transaction.shipping["street_address"]
        self.cart.ship_street2 = transaction.shipping["extended_address"]
        self.cart.ship_city = transaction.shipping["locality"]
        self.cart.ship_state = transaction.shipping["region"]
        self.cart.ship_postal_code = transaction.shipping["postal_code"]
        self.cart.ship_country = transaction.shipping["country_code_alpha2"]
        self.cart.bill_first_name = transaction.billing["first_name"]
        self.cart.bill_last_name = transaction.billing["last_name"]
        self.cart.bill_street1 = transaction.billing["street_address"]
        self.cart.bill_street2 = transaction.billing["extended_address"]
        self.cart.bill_city = transaction.billing["locality"]
        self.cart.bill_state = transaction.billing["region"]
        self.cart.bill_postal_code = transaction.billing["postal_code"]
        self.cart.bill_country = transaction.billing["country_code_alpha2"]
        self.cart.save()
        self.create_payment(transaction)