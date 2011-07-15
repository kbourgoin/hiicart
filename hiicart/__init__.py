__version__ = '0.2.12'


def validate_gateway(gateway):
    """Test that a gateway is correctly set up.
    Returns True if successful, or an error message."""
    from hiicart.gateway.base import GatewayError
    from hiicart.gateway.amazon.gateway import AmazonGateway
    from hiicart.gateway.google.gateway import GoogleGateway
    from hiicart.gateway.paypal.gateway import PaypalGateway
    from hiicart.gateway.paypal2.gateway import Paypal2Gateway
    from hiicart.gateway.paypal_adaptive.gateway import PaypalAPGateway
    from hiicart.gateway.braintree.gateway import BraintreeGateway
    if gateway == "amazon":
        cls = AmazonGateway
    elif gateway == "google":
        cls = GoogleGateway
    elif gateway == "paypal":
        cls = PaypalGateway
    elif gateway == "paypal2":
        cls = Paypal2Gateway
    elif gateway == "paypal_adaptive":
        cls = PaypalAPGateway
    elif gateway == "braintree":
        cls = BraintreeGateway
    try:
        obj = cls()
        return obj._is_valid() or "Authentication Error"
    except GatewayError, err:
        return err.message
