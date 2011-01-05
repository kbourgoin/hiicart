import re

from datetime import datetime
from decimal import Decimal

from hiicart.gateway.base import IPNBase
from hiicart.gateway.google.errors import GoogleGatewayError 
from hiicart.gateway.google.settings import SETTINGS as default_settings
from hiicart.models import HiiCart, Payment

class GoogleIPN(IPNBase):
    """Google Checkout IPN Handler."""

    def __init__(self):
        super(GoogleIPN, self).__init__("google", default_settings)
        self._require_settings(["MERCHANT_ID", "MERCHANT_KEY"])

    def _find_payment(self, data):
        """Find a payment based on the google id"""
        transaction_id = data["google-order-number"]
        payments = Payment.objects.filter(transaction_id=transaction_id)
        return payments[0] if payments else None

    def _find_cart(self, data):
        """Find purchase using a google id"""
        payment = self._find_payment(data)
        return payment.cart if payment else None

    def _find_cart_neworder(self, data):
        """
        Find the Purchase for a new order.

        Complex because every payment for a subscription comes across
        as a new order. Need to find order id somewhere
        """
        private_data = None
        if "shopping-cart.merchant-private-data" in data:        
            private_data = data["shopping-cart.merchant-private-data"]
        else:
            items = [x for x in data.keys() if x.endswith("merchant-private-item-data")]
            if len(items) > 0:
                private_data = data[items[0]]
        if not private_data:
            return None # Not a HiiCart purchase ?
        # Find Purchase from private data
        match = re.search(r'(hiicart|bursar)-purchase id="([0-9a-f-]+)"',  private_data)
        if not match:
            return
        carts = HiiCart.objects.filter(_cart_uuid=match.group(2))
        return carts[0] if carts else None

    def _record_payment(self, data, cart=None, amount=None, state="PAID"):
        """Record a payment from the IPN data."""
        if not cart:
            cart = self._find_cart(data)
            if not cart:
                return
        if not amount:
            amount = data["latest-charge-amount"]
        transaction_id = data["google-order-number"]
        pending = cart.payments.filter(state="PENDING", transaction_id=transaction_id)
        if pending:
            pending[0].state = "PAID"
            pending[0].save()
            return pending[0]
        else:
            payment = self._create_payment(cart, amount, transaction_id, state)
            payment.save()
            return payment

    def authorization_amount(self, data):
        """
        Handle an authorization-amount-notification

        These requests are sent in response to explicit credit card 
        reauthorizations.
        """
        pass

    def cancelled_subscription(self, data):
        """Handle cancelled-subscription-notification"""
        cart = self._find_cart(data)
        if not cart:
            return
        items = []
        if isinstance(data["item-ids"], list):
            item_ids = data["item-ids"]
        else:
            item_ids = [data["item-ids"]]
        for item_id in item_ids:
            sku_key = "%s.merchant-item-id" % item_id         
            if sku_key in data:
                item = cart.recurringlineitems.get(sku=data[sku_key])
                items.append(item)
        for i in items:
            i.is_active = False
            i.save()
        cart.update_state()

    def charge_amount(self, data):
        """
        Handle charge-amount-notification
        """
        amount = Decimal(data["latest-charge-amount"])
        pmnt = self._record_payment(data, amount=amount)
        if not pmnt:
            return
        for r in pmnt.cart.recurringlineitems.all():
            r.is_active = True
            r.save()
        pmnt.cart.update_state()

    def chargeback_amount(self, data):
        """
        Handle a chargeback-amount-notification

        Handled exactly the same as a refund
        """    
        return self.refund_amount(data)

    def new_order(self, data):
        """
        Handle new-order-notification
        
        Looks up the Purchase and creates a pending payment.
        """
        # TODO: Order adjustments from shipping/tax
        # TODO: Does not support different ship/bill name or email
        cart = self._find_cart_neworder(data)
        if not cart:
            return
        payment = self._record_payment(data, cart=cart,
                                       amount=data["order-total"],
                                       state="PENDING")
        if not payment:
            return
        # Save buyer information if not already there
        cart.first_name = cart.first_name or data["buyer-billing-address.structured-name.first-name"]
        cart.last_name = cart.last_name or data["buyer-billing-address.structured-name.last-name"]
        cart.email = cart.email or data["buyer-billing-address.email"]
        cart.phone = cart.phone or data["buyer-shipping-address.phone"]
        cart.ship_street1 = cart.ship_street1 or data["buyer-shipping-address.address1"]
        cart.ship_street2 = cart.ship_street2 or data["buyer-shipping-address.address2"]
        cart.ship_city = cart.ship_city or data["buyer-shipping-address.city"]
        cart.ship_state = cart.ship_state or data["buyer-shipping-address.region"]
        cart.ship_postal_code = cart.ship_postal_code or data["buyer-shipping-address.postal-code"]
        cart.ship_country = cart.ship_country or data["buyer-shipping-address.country-code"]
        cart.bill_street1 = cart.bill_street1 or data["buyer-billing-address.address1"]
        cart.bill_street2 = cart.bill_street2 or data["buyer-billing-address.address2"]
        cart.bill_city = cart.bill_city or data["buyer-billing-address.city"]
        cart.bill_state = cart.bill_state or data["buyer-billing-address.region"]
        cart.bill_postal_code = cart.bill_postal_code or data["buyer-billing-address.postal-code"]
        cart.bill_country = cart.bill_country or data["buyer-billing-address.country-code"]
        cart.save()
        
    def order_state_change(self, data):        
        """Handle an order-state-change notification"""
        old = data["previous-financial-order-state"]
        new = data["new-financial-order-state"]
        payment = self._find_payment(data)
        if payment is None:
            return # Not a HiiCart purchase (?)
        cart = payment.cart
        if old != "CANCELLED" and new == "CANCELLED":
            cart.notes.create(text="Purchase cancelled via IPN: %s" % datetime.now())
            for r in cart.recurringlineitems.all(): 
                r.is_active = False
                r.save()
            cart.set_state("CANCELLED")

    def refund_amount(self, data):
        """
        Handle a refund-amount-notification

        Handled as a charge amount for a negative amount with
        the reason_code set to "REFUND"
        """  
        amount = Decimal(data["latest-refund-amount"]) * -1
        pmnt = self._record_payment(data, amount=amount)
        if pmnt:
           pmnt.cart.update_state() 

    def risk_information(self, data):
        """
        Handle a risk-information-notification

        Save the information as a note on the payment. It's useful information
        for auditing purposes, but not much outside of that.
        """
        payment = self._find_payment(data)
        if not payment:
            return
        keys = [k for k in data.keys() if k[:17] == "risk-information."] 
        keys.sort()
        message = "Risk Information: \n" + "\n".join(["%s: %s" % (k, data[k]) for k in keys])
        payment.notes.create(text=message)
