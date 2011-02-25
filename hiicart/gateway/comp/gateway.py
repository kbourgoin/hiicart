from hiicart.gateway.base import GatewayError, PaymentGatewayBase
from hiicart.gateway.comp.settings import SETTINGS as default_settings

class CompGatewayError(GatewayError):
    pass

class CompGateway(PaymentGatewayBase):
    """
    A gateway for complementary purchases.

    This gateway doesn't make a payment anywhere. It simply records
    a payment of cart.total as successfully paid.
    """
    def __init__(self, cart):
        super(CompGateway, self).__init__("comp", cart, default_settings)

    def cancel_recurring(self):
        """Cancel recurring items."""
        for ri in self.cart.recurring_lineitems:
            ri.is_active = False
            ri.save()
        self.cart.update_state()

    def charge_recurring(self, grace_period):
        """
        Charge recurring purchases if necessary.

        Charges recurring items with the gateway, if possible. An optional
        grace period can be provided to avoid premature charging. This is
        provided since the gateway might be in another timezone, causing
        a mismatch between when an account can be charged.
        """
        if any([r.is_expired(grace_period) and r.is_active for r in self.cart.recurring_lineitems]):
            payment = self._create_payment(self.cart, self.cart.total, None, "PAID")
            payment.save()

    def sanitize_clone(self):
        """Nothing gateway-specific here."""
        pass

    def submit(self, collect_address=False):
        """Submit cart. Returns None because comp is instantaneous."""
        payment = self._create_payment(self.cart, self.cart.total, None, "PAID")
        if self.settings.get("ALLOW_RECURRING_COMP", False):
            for ri in self.cart.recurring_lineitems:
                ri.is_active = True
                ri.save()
        self.cart.update_state()
