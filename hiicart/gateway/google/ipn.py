from datetime import datetime
from decimal import Decimal
from hiicart.gateway.base import IPNBase
from hiicart.gateway.google.settings import SETTINGS as default_settings
from hiicart.models import CART_TYPES


class GoogleIPN(IPNBase):
    """Google Checkout IPN Handler."""

    def __init__(self, cart):
        super(GoogleIPN, self).__init__("google", cart, default_settings)
        self._require_settings(["MERCHANT_ID", "MERCHANT_KEY"])

    @staticmethod
    def _find_payment(data):
        """Find a payment based on the google id"""
        transaction_id = data["google-order-number"]
        for Cart in CART_TYPES:
            try:
                return Cart.payment_class.objects.select_related('cart').get(transaction_id=transaction_id)
            except:
                pass

    def _record_payment(self, data, amount=None, state="PAID"):
        """Record a payment from the IPN data."""
        if not self.cart:
            return
        if not amount:
            amount = data["latest-charge-amount"]
        transaction_id = data["google-order-number"]
        pending = self.cart.payments.filter(state="PENDING", transaction_id=transaction_id)
        if pending:
            pending[0].state = "PAID"
            pending[0].save()
            return pending[0]
        else:
            payment = self._create_payment(amount, transaction_id, state)
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
        if not self.cart:
            return
        items = []
        if isinstance(data["item-ids"], list):
            item_ids = data["item-ids"]
        else:
            item_ids = [data["item-ids"]]
        recurring_by_sku = dict([(li.sku, li) for li in self.cart.recurring_lineitems])
        for item_id in item_ids:
            sku_key = "%s.merchant-item-id" % item_id
            if sku_key in data:
                item = recurring_by_sku.get(data[sku_key])
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
        for r in pmnt.cart.recurring_lineitems:
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
        if not self.cart:
            return
        # Save buyer information if not already there
        if data.get("buyer-shipping-address.structured-name.first-name"):
            self.cart.ship_first_name = self.cart.ship_first_name or data['buyer-shipping-address.structured-name.first-name']
        else:
            self.cart.ship_first_name = self.cart.ship_first_name or data['buyer-shipping-address.contact-name']
        if data.get("buyer-shipping-address.structured-name.last-name"):
            self.cart.ship_last_name = self.cart.ship_last_name or data['buyer-shipping-address.structured-name.last-name']

        if data.get("buyer-billing-address.structured-name.first-name"):
            self.cart.bill_first_name = self.cart.bill_first_name or data['buyer-billing-address.structured-name.first-name']
        else:
            self.cart.bill_first_name = self.cart.bill_first_name or data['buyer-billing-address.contact-name']
        if data.get("buyer-billing-address.structured-name.last-name"):
            self.cart.bill_last_name = self.cart.bill_last_name or data['buyer-billing-address.structured-name.last-name']

        self.cart.ship_email = self.cart.ship_email or data["buyer-shipping-address.email"]
        self.cart.ship_phone = self.cart.ship_phone or data["buyer-shipping-address.phone"]
        self.cart.ship_street1 = self.cart.ship_street1 or data["buyer-shipping-address.address1"]
        self.cart.ship_street2 = self.cart.ship_street2 or data["buyer-shipping-address.address2"]
        self.cart.ship_city = self.cart.ship_city or data["buyer-shipping-address.city"]
        self.cart.ship_state = self.cart.ship_state or data["buyer-shipping-address.region"]
        self.cart.ship_postal_code = self.cart.ship_postal_code or data["buyer-shipping-address.postal-code"]
        self.cart.ship_country = self.cart.ship_country or data["buyer-shipping-address.country-code"]
        self.cart.bill_email = self.cart.bill_email or data["buyer-billing-address.email"]
        self.cart.bill_phone = self.cart.bill_phone or data["buyer-billing-address.phone"]
        self.cart.bill_street1 = self.cart.bill_street1 or data["buyer-billing-address.address1"]
        self.cart.bill_street2 = self.cart.bill_street2 or data["buyer-billing-address.address2"]
        self.cart.bill_city = self.cart.bill_city or data["buyer-billing-address.city"]
        self.cart.bill_state = self.cart.bill_state or data["buyer-billing-address.region"]
        self.cart.bill_postal_code = self.cart.bill_postal_code or data["buyer-billing-address.postal-code"]
        self.cart.bill_country = self.cart.bill_country or data["buyer-billing-address.country-code"]
        self.cart.save()
        self._record_payment(data,
                             amount=data["order-total"],
                             state="PENDING")

    def order_state_change(self, data):
        """Handle an order-state-change notification"""
        old = data["previous-financial-order-state"]
        new = data["new-financial-order-state"]
        payment = self._find_payment(data)
        if payment is None:
            return # Not a HiiCart purchase (?)
        if old != "CANCELLED" and new == "CANCELLED":
            self.cart.notes.create(text="Purchase cancelled via IPN: %s" % datetime.now())
            for r in self.cart.recurring_lineitems:
                r.is_active = False
                r.save()
            self.cart.set_state("CANCELLED")

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
