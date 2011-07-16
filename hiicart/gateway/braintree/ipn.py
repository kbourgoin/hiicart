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

    def _record_payment(self, transaction):
        """Record a payment from the IPN data."""
        if not self.cart:
            return
        if transaction.order_id != self.cart.cart_uuid:
            log.error("Cart uuid mismatch from Braintree payment result: " % str(data.items()))
            state = "FAILED"
        elif transaction.status == "submitted_for_settlement" \
            or transaction.status == "settled" or transaction.status == "authorized":
            state = "PAID"
        elif transaction.status == "authorizing":
            state = "PENDING"
        else:
            state = "FAILED"
        payment = self._create_payment(transaction.amount, transaction.id, state)
        payment.save()
        return payment

    def confirm_payment(self, data):
        # Send payment confirmation
        result = braintree.TransparentRedirect.confirm(data)
        payment = self._record_payment(result.transaction)
