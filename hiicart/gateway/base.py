import logging
import os

from django.conf import settings

from hiicart.models import Payment
from hiicart.utils import call_func

class GatewayError(Exception):
    pass

# Should these have a common base class? Seems excessive vs. code duplication.

class _SharedBase(object):
    """Shared base class between IPNs and Gateways that accommodates their significant shared functionality."""

    def __init__(self, name, default_settings={}):
        self.name = name.upper()
        self.log = logging.getLogger("hiicart.gateway." + self.name)
        if self.name not in settings.HIICART_SETTINGS:
            raise GatewayError("Settings not defined for %s" % self.name)
        self.settings = default_settings.copy()
        self.settings.update(settings.HIICART_SETTINGS[self.name])
        # Copy down some settings, if not overridden locally
        if "LIVE" not in self.settings: # app-level setting with gateway-level override
            self.settings["LIVE"] = settings.HIICART_SETTINGS["LIVE"]
        if "EXPIRATION_GRACE_PERIOD" not in self.settings and "EXPIRATION_GRACE_PERIOD" in settings.HIICART_SETTINGS:
            self.settings["EXPIRATION_GRACE_PERIOD"] = settings.HIICART_SETTINGS["EXPIRATION_GRACE_PERIOD"]
        if "CHARGE_RECURRING_GRACE_PERIOD" not in self.settings and "CHARGE_RECURRING_GRACE_PERIOD" in settings.HIICART_SETTINGS:
            self.settings["CHARGE_RECURRING_GRACE_PERIOD"] = settings.HIICART_SETTINGS["CHARGE_RECURRING_GRACE_PERIOD"]

    def _create_payment(self, cart, amount, transaction_id, state):
        """Record a payment."""
        pmnt = Payment(amount=amount, gateway=self.name, cart=cart, 
                       state=state, transaction_id=transaction_id)
        pmnt.save()
        return pmnt

    def _update_with_cart_settings(self, hiicart):
        """Pull cart-specific settings and update self.settings with them.
        We need an DI facility to get cart-specific settings in. This way,
        we're able to have different carts use different google accounts."""
        if not settings.HIICART_SETTINGS.get("CART_SETTINGS_FN", False):
            return
        s = call_func(settings.HIICART_SETTINGS["CART_SETTINGS_FN"], hiicart)
        self.settings.update(s)

    def _require_files(self, filenames):
        """Verify a file exists on disk. Usually use for key files."""
        errors = []
        for filename in filenames:
            if not os.path.isfile(filename):
                errors.append(filename)
        if len(errors) > 0:
            raise GatewayError("The following files are required for %s: %s" % (
                                self.name, ", ".join(errors)))

    def _require_settings(self, settings):
        """Verify that certain settings exist, raising an error if not."""
        errors = []
        for setting in settings:
            if setting not in self.settings:
                errors.append(setting)
        if len(errors) > 0:
            raise GatewayError("The following settings are required for %s: %s" % (
                                self.name, ", ".join(errors)))


class IPNBase(_SharedBase):
    """
    Base class for IPN handlers.

    Provides shared functionality among IPN implementations
    """
    pass # All covered by _SharedBase for now


class PaymentGatewayBase(_SharedBase):
    """
    Base class for all payment gateways.

    Provides a common interface for working with all payment gateways.
    """
    def cancel_recurring(self, cart):
        """Cancel recurring items with gateway. Returns a CancelResult."""
        raise NotImplementedError

    def charge_recurring(self, cart, grace_period=None):
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

    def submit(self, cart, collect_address=False):
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
    Currently supported result types are url, form, and None.
    
    url: The user should to be redirected to result.url.
    form: form_action is the target url; form_fields is a dict of form data.
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
