import braintree

from django.template import Context, loader

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult, PaymentResult
from hiicart.gateway.braintree.forms import PaymentForm
from hiicart.gateway.braintree.ipn import BraintreeIPN
from hiicart.gateway.braintree.settings import SETTINGS as default_settings


class BraintreeGateway(PaymentGatewayBase):
    """Payment Gateway for Braintree."""

    def __init__(self, cart):
        super(BraintreeGateway, self).__init__("braintree", cart, default_settings)
        self._require_settings(["MERCHANT_ID", "MERCHANT_KEY",
                                "MERCHANT_PRIVATE_KEY"])
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
        """Determine which Braintree environment to use."""
        if self.settings["LIVE"]:
            return braintree.Environment.Production
        else:
            return braintree.Environment.Sandbox

    def submit(self, collect_address=False, cart_settings_kwargs=None, submit=False):
        """
        Simply returns the gateway type to let the frontend know how to proceed.
        """
        return SubmitResult("direct")

    @property
    def form(self):
        """Returns an instance of PaymentForm."""
        return PaymentForm()

    def start_transaction(self, request):
        """Submits transaction details to Braintree and returns form data."""
        tr_data = braintree.Transaction.tr_data_for_sale({
            "transaction": {"type": "sale",
                            "order_id": self.cart.cart_uuid,
                            "amount": self.cart.total,
                            "options": {"submit_for_settlement": True}}},
            request.build_absolute_uri(request.path))
        return tr_data

    def confirm_payment(self, request):
        """
        Confirms payment result with Braintree.

        This method should be called after the Braintree transaction redirect
        to determine the payment result. It expects the request to contain the
        query string coming back from Braintree.
        """
        try:
            result = braintree.TransparentRedirect.confirm(request.META['QUERY_STRING'])
        except Exception, e:
            errors = {'non_field_errors': 'Request to payment gateway failed.'}
            return PaymentResult(transaction_id=None, success=False,
                                 status=None, errors=errors)

        if result.is_success:
            handler = BraintreeIPN(self.cart)
            created = handler.new_order(result.transaction)
            if created:
                return PaymentResult(transaction_id=result.transaction.id,
                                     success=True,
                                     status=result.transaction.status)
        errors = {}
        if not result.transaction:
            transaction_id = None
            status = None
            for error in result.errors.deep_errors:
                errors[error.attribute] = error.message
        else:
            transaction_id = result.transaction.id
            status = result.transaction.status
            if result.transaction.status == "processor_declined":
                errors = {'non_field_errors': result.transaction.processor_response_text}
            elif result.transaction.status == "gateway_rejected":
                errors = {'non_field_errors': result.transaction.gateway_rejection_reason}
        return PaymentResult(transaction_id=transaction_id, success=False,
                             status=status, errors=errors)
