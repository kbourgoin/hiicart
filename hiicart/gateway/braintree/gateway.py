import braintree

from django.template import Context, loader

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult
from hiicart.gateway.braintree.ipn import BraintreeIPN
from hiicart.gateway.braintree.settings import SETTINGS as default_settings


class BraintreeGateway(PaymentGatewayBase):
    """Payment Gateway for Braintree."""

    def __init__(self, cart):
        super(BraintreeGateway, self).__init__("braintree", cart, default_settings)
        self._require_settings(["MERCHANT_ID", "MERCHANT_KEY", "MERCHANT_PRIVATE_KEY"])
        braintree.Configuration.configure(self.environment, 
                                          self.settings["MERCHANT_ID"], 
                                          self.settings["MERCHANT_KEY"],
                                          self.settings["MERCHANT_PRIVATE_KEY"])

    def _is_valid(self):
        """Return True if gateway is valid."""
        # TODO: Query Braintree to validate credentials
        return True

    @property
    def environment(self):
        if self.settings["LIVE"]:
            return braintree.Environment.Production
        else:
            return braintree.Environment.Sandbox

    def store_return_url(self, request):
        self._update_with_cart_settings({"request": request})
        return self.settings["RETURN_URL"]

    def submit(self, collect_address=False, cart_settings_kwargs=None, submit=False):
        """Returns the type of Gateway"""
        return SubmitResult("direct")

    def form_data(self, return_url):
        """Submits transaction details to Braintree and gets form data."""
        submit_url = braintree.TransparentRedirect.url()
        tr_data = braintree.Transaction.tr_data_for_sale({
            "transaction": {"type": "sale",
                            "order_id": self.cart.cart_uuid,
                            "amount": self.cart.total,
                            "options": {"submit_for_settlement": True}}}, 
            return_url)
        return {"action": submit_url, 
                "fields": {"tr_data": tr_data}}

    def confirm_payment(self, request):
        """Confirms payment with Braintree."""
        try:
            result = braintree.TransparentRedirect.confirm(request.META['QUERY_STRING'])
        except:
            return False

        if result.is_success:
            handler = BraintreeIPN(self.cart)
            created = handler.new_order(result.transaction)
            if created:
                self.cart.set_state("SUBMITTED")
                return True     
        return False
