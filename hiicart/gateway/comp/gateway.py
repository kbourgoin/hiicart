from hiicart.gateway.base import GatewayError, PaymentGatewayBase

class CompGatewayError(GatewayError):
    pass

class CompGateway(PaymentGatewayBase):
    """
    A gateway for complementary purchases.

    This gateway doesn't make a payment anywhere. It simply records 
    a payment of cart.total as successfully paid.
    """
    def __init__(self):
        super(CompGateway, self).__init__("comp")

    def cancel_recurring(self, cart):
        """Cancel recurring items."""
        for ri in cart.recurringlineitems.all():
            ri.is_active = False 
            ri.save()
        cart.update_state()

    def charge_recurring(self, cart, grace_period):
        """
        Charge recurring purchases if necessary.
        
        Charges recurring items with the gateway, if possible. An optional
        grace period can be provided to avoid premature charging. This is
        provided since the gateway might be in another timezone, causing
        a mismatch between when an account can be charged.
        """
        if any([r.is_expired(grace_period) and r.is_active for r in cart.recurringlineitems.all()]):
            payment = self._create_payment(cart, cart.total, None, "PAID")
            payment.save()

    def sanitize_clone(self, cart):
        """Nothing gateway-specific here."""
        pass

    def submit(self, cart, collect_address=False):
        """Submit cart. Returns None because comp is instantaneous."""
        payment = self._create_payment(cart, cart.total, None, "PAID")
        if self.settings.get("ALLOW_RECURRING_COMP", False):
            for ri in cart.recurringlineitems.all():
                ri.is_active = True
                ri.save()
        cart.update_state()
