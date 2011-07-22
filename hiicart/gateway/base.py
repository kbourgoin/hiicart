import logging
import os
from hiicart.utils import call_func


class GatewayError(Exception):
    pass


class _SharedBase(object):
    """Shared base class between IPNs and Gateways

    Created because they have significant overlapping functionality.
    """

    def __init__(self, name, cart, default_settings=None):
        """Initalize logger and settings.

        Duplicate settings are overwritten according to priority according to
        the following ascending priority:
        default_settings -> global -> gateway defined in HIICART_SETTINGS
        """
        self.name = name.upper()
        self.log = logging.getLogger("hiicart.gateway." + self.name)
        self.settings = default_settings or {}
        self.settings.update(cart.hiicart_settings)
        if self.name in self.settings:
            self.settings.update(cart.hiicart_settings[self.name])
        self._settings_base = self.settings.copy()
        self.cart = cart
        self._update_with_store_settings()

    def _create_payment(self, amount, transaction_id, state):
        """Record a payment."""
        pmnt = self.cart.payment_class(amount=amount, gateway=self.name, cart=self.cart,
                                       state=state, transaction_id=transaction_id)
        pmnt.save()
        return pmnt

    def _update_with_store_settings(self):
        """Pull cart-specific settings and update self.settings with them.
        We need an DI facility to get cart-specific settings in. This way,
        we're able to have different carts use different google accounts."""
        if self.cart.hiicart_settings.get("STORE_SETTINGS_FN"):
            s = call_func(self.cart.hiicart_settings["STORE_SETTINGS_FN"], self.cart)
            if s:
                self.settings.update(s)
                return
        self.settings = self._settings_base.copy()  # reset to defaults

    def _update_with_cart_settings(self, cart_settings_kwargs):
        """Pull cart-specific settings and update self.settings with them.
        We need an DI facility to get cart-specific settings in. This way,
        we're able to have different carts use different google accounts."""
        if self.cart.hiicart_settings.get("CART_SETTINGS_FN"):
            cart_settings_kwargs = cart_settings_kwargs or {}
            s = call_func(self.cart.hiicart_settings["CART_SETTINGS_FN"],
                          self.cart, **cart_settings_kwargs)
            if s:
                self.settings.update(s)
                return
        self.settings = self._settings_base.copy()  # reset to defaults

    def _require_files(self, filenames):
        """Verify a file exists on disk. Usually use for key files."""
        errors = []
        for filename in filenames:
            if not os.path.isfile(filename):
                errors.append(filename)
        if len(errors) > 0:
            raise GatewayError("The following files are required for %s: %s" % (
                                self.name, ", ".join(errors)))

    def _require_settings(self, required_settings):
        """Verify that certain settings exist, raising an error if not."""
        errors = []
        for setting in required_settings:
            if not self.settings.get(setting, False):
                errors.append(setting)
        if len(errors) > 0:
            raise GatewayError("The following settings are required for %s: %s" % (
                                self.name, ", ".join(errors)))


class IPNBase(_SharedBase):
    """
    Base class for IPN handlers.

    Provides shared functionality among IPN implementations
    """
    pass  # All covered by _SharedBase for now


class PaymentGatewayBase(_SharedBase):
    """
    Base class for all payment gateways.

    Provides a common interface for working with all payment gateways.
    """
    def __init__(self, name, cart, default_settings=None):
        super(PaymentGatewayBase, self).__init__(name, cart, default_settings)

    def _is_valid(self):
        """Returns True if the gateway is set up properly.
        NOTE: Will return Fase if using cart-specific settings and omitting
        required settings from global definition."""
        raise NotImplementedError

    def cancel_recurring(self):
        """Cancel recurring items with gateway. Returns a CancelResult."""
        raise NotImplementedError

    def charge_recurring(self, grace_period=None):
        """
        Charge recurring purchases if necessary.

        Charges recurring items with the gateway, if possible. An optional
        grace period can be provided to avoid premature charging. This is
        provided since the gateway might be in another timezone, causing
        a mismatch between when an account can be charged.
        """
        raise NotImplementedError

    def sanitize_clone(self, cart):
        """Remove any gateway-specific changes to a cloned cart."""
        raise NotImplementedError

    def submit(self, collect_address=False, cart_settings_kwargs=None):
        """Submit a cart to the gateway. Returns a SubmitResult."""
        raise NotImplementedError


class CancelResult(object):
    """
    The result of a cancel operation.
    Currently supported result types are url and None.

    url: The user should to be redirected to result.url.
    None: type is set to None if no further action is required.
    """
    def __init__(self, type, url=None):
        if type is not None and type != "url":
            raise GatewayError("Unknown return type %s" % type)
        self.type = type
        self.url = url


class SubmitResult(object):
    """
    The result of a submit operation.
    Currently supported result types are url, form, direct, and None.

    url: The user should to be redirected to result.url.
    form: form_action is the target url; form_fields is a dict of form data.
    direct: form_action is the form target; form_fields is a dict of hidden form
            required by the gateway.
    None: type is set to None if no further action is required.
    """
    def __init__(self, type, url=None, form_data=None):
        self.type = type
        if url and form_data:
            raise GatewayError("Gateway returned url AND form data.")
        self.url = url
        if type == "form":
            self.form_action = form_data["action"]
            self.form_fields = form_data["fields"]
        else:
            self.form_action = None
            self.form_fields = None


class PaymentResult(object):
    """
    Result for a payment confirmation.
    Currently only supported with direct payment gateways.
    """
    def __init__(self, transaction_id, success, status, errors=None):
        self.transaction_id = transaction_id
        self.success = success
        self.status = status
        self.errors = errors
