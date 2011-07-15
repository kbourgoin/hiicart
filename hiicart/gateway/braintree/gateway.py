import braintree

from django.template import Context, loader

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult
from hiicart.gateway.braintree.settings import SETTINGS as default_settings


class BraintreeGateway(PaymentGatewayBase):
    """Payment Gateway for Braintree."""

    def __init__(self, cart):
        super(BraintreeGateway, self).__init__("braintree", cart, default_settings)
        self._require_settings(["MERCHANT_ID", "MERCHANT_PUBLIC_KEY", "MERCHANT_PRIVATE_KEY"])

    def _is_valid(self):
        """Return True if gateway is valid."""
        # TODO: Query Braintree to validate credentials
        return True

    def submit(self, collect_address=False, cart_settings_kwargs=None):
        """Submit a cart to Braintree."""
        self._update_with_cart_settings(cart_settings_kwargs)
        if self.settings["LIVE"]:
            env = braintree.Environment.Production
        else:
            env = braintree.Environment.Sandbox
        braintree.Configuration.configure(env, self.settings["MERCHANT_ID"],
                                          self.settings["MERCHANT_PUBLIC_KEY"],
                                          self.settings["MERCHANT_PRIVATE_KEY"])
        return SubmitResult("direct")
        #result = braintree.Transaction.sale({
            #"order_id": self.cart.cart_uuid,
            #"amount": "",
            #"options": {"submit_for_settlement": True},
            #"credit_card": {
                #"number": "",
                #"expiration_date": "",
                #"cardholder_name": "",
                #"cvv": "cvv",
            #}});
