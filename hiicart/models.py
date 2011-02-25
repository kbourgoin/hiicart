import copy
import django
import logging
import uuid

from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django import dispatch
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields import DecimalField
from django.utils.safestring import mark_safe
from hiicart.settings import SETTINGS as hiicart_settings
from logging.handlers import RotatingFileHandler

log = logging.getLogger("hiicart.models")

### Set up library-wide logging

if hiicart_settings["LOG"]:
    level = hiicart_settings["LOG_LEVEL"]
    logger = logging.getLogger("hiicart")
    logger.setLevel(level)
    ch = RotatingFileHandler(
            hiicart_settings["LOG"],
            maxBytes=5242880,
            backupCount=10,
            encoding="utf-8")
    ch.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

### Lists for field choices

SHIPPING_CHOICES = (("0", "No Shipping Charges"),
                    ("1", "Pay Shipping Once"),
                    ("2", "Pay Shipping Each Billing Cycle"))

SUBSCRIPTION_UNITS = (("DAY", "Days"),
                      ("MONTH", "Months"))

HIICART_STATES = (("OPEN", "Open"),
                  ("SUBMITTED", "Submitted"),
                  ("ABANDONED", "Abandoned"),
                  ("COMPLETED", "Completed"),
                  ("RECURRING", "Recurring"), # Subscription active
                  ("PENDCANCEL", "Pending Cancellation"), # Subscription cancelled, but not expired yet
                  ("CANCELELD", "Cancelled"))

PAYMENT_STATES = (("PENDING", "Pending"),
                  ("PAID", "Paid"),
                  ("FAILED", "Failed"),
                  ("CANCELLED", "Cancelled"))

# What state transitions are valid for a cart
VALID_TRANSITIONS = {"OPEN": ["SUBMITTED", "ABANDONED", "COMPLETED",
                              "RECURRING", "PENDCANCEL", "CANCELLED"],
                     "SUBMITTED": ["PAID", "COMPLETED", "RECURRING",
                                   "PENDCANCEL", "CANCELLED"],
                     "ABANDONED": [],
                     "COMPLETED": ["RECURRING", "PENDCANCEL", "CANCELLED"],
                     "RECURRING": ["PENDCANCEL", "CANCELLED"],
                     "PENDCANCEL": ["CANCELLED"],
                     "CANCELLED": []}

### Signals

cart_state_changed = dispatch.Signal(providing_args=["cart", "new_state",
                                                     "old_state"])
payment_state_changed = dispatch.Signal(providing_args=["payment", "new_state",
                                                        "old_state"])

### Exceptions

class HiiCartError(Exception):
    pass

### Private Functions

### Models

# Stop CASCADE ON DELETE with User, but keep compatibility with django < 1.3
if django.VERSION[1] >= 3 and hiicart_settings["KEEP_ON_USER_DELETE"]:
    _user_delete_behavior = models.SET_NULL
else:
    _user_delete_behavior = None

class HiiCart(models.Model):
    """
    Collects information about an order and tracks its state.

    Facilitates the cart being submitted to a payment gateway and some
    subscription management functions.
    """
    lineitem_types = []
    recurring_lineitem_types = []
    one_time_lineitem_types = []

    _cart_state = models.CharField(choices=HIICART_STATES, max_length=16, default="OPEN", db_index=True)
    _cart_uuid = models.CharField(max_length=36,db_index=True)
    gateway = models.CharField(max_length=16, null=True, blank=True)
    notes = generic.GenericRelation("Note")
    if _user_delete_behavior is not None:
        user = models.ForeignKey(User, related_name="hiicarts", on_delete=_user_delete_behavior, null=True, blank=True)
    else:
        user = models.ForeignKey(User, related_name="hiicarts", null=True, blank=True)
    # Redirection targets after purchase completes
    failure_url = models.URLField(null=True)
    success_url = models.URLField(null=True)
    # Total fields
    # sub_total and total are '_' so we can recalculate them on the fly
    _sub_total = DecimalField("Subtotal", max_digits=18, decimal_places=2, blank=True, null=True)
    _total = DecimalField("Total", max_digits=18, decimal_places=2)
    tax = DecimalField("Tax", max_digits=18, decimal_places=2, blank=True, null=True)
    shipping = DecimalField("Shipping Cost", max_digits=18, decimal_places=2, blank=True, null=True)
    # Customer Info
    first_name = models.CharField("First name", max_length=30, default="")
    last_name = models.CharField("Last name", max_length=30, default="")
    email = models.EmailField("Email", max_length=75, default="")
    phone = models.CharField("Phone Number", max_length=30, default="")
    ship_street1 = models.CharField("Street", max_length=80, default="")
    ship_street2 = models.CharField("Street 2", max_length=80, default="")
    ship_city = models.CharField("City", max_length=50, default="")
    ship_state = models.CharField("State", max_length=50, default="")
    ship_postal_code = models.CharField("Zip Code", max_length=30, default="")
    ship_country = models.CharField("Country", max_length=2, default="")
    bill_street1 = models.CharField("Street", max_length=80, default="")
    bill_street2 = models.CharField("Street", max_length=80, default="")
    bill_city = models.CharField("City", max_length=50, default="")
    bill_state = models.CharField("State", max_length=50, default="")
    bill_postal_code = models.CharField("Zip Code", max_length=30, default="")
    bill_country = models.CharField("Country", max_length=2, default="")
    created = models.DateTimeField("Created", auto_now_add=True)
    last_updated = models.DateTimeField("Last Updated", auto_now=True)

    def __init__(self, *args, **kwargs):
        """Override in order to keep track of changes to state."""
        super(HiiCart, self).__init__(*args, **kwargs)
        self._old_state = self.state

    def __unicode__(self):
        if self.id:
            return "#%s %s" % (self.id, self.state)
        else:
            return "(unsaved) %s" % self.state

    @staticmethod
    def register_lineitem_type(recurring=False):
        def register_decorator(cls):
            HiiCart.lineitem_types.append(cls)
            if recurring:
                HiiCart.recurring_lineitem_types.append(cls)
            else:
                HiiCart.one_time_lineitem_types.append(cls)
            return cls
        return register_decorator

    @property
    def lineitems(self):
        return self._get_lineitems(HiiCart.lineitem_types)

    @property
    def recurring_lineitems(self):
        return self._get_lineitems(HiiCart.recurring_lineitem_types)

    @property
    def one_time_lineitems(self):
        return self._get_lineitems(HiiCart.one_time_lineitem_types)

    def _get_lineitems(self, cls_list):
        l = [cls.objects.filter(cart=self) for cls in cls_list]
        return [item for sublist in l for item in sublist]

    def _is_valid_transition(self, old, new):
        """
        Validate a proposed state transition.

        This prevents cases like an account going from CANCELLED to
        PENDCANCEL when a user cancels the subscription. As far as the
        system is concerned, it should be pending cancellation, but it's
        been marked as cancelled by another part of the system or an admin.
        See VALID_TRANSITIONS.
        """
        return new in VALID_TRANSITIONS[old]

    def _recalc(self):
        """Recalculate totals"""
        self._sub_total = self.sub_total
        self._total = self.total

    @property
    def cart_uuid(self):
        """UUID identifying this cart to gateways. Populated on initial save."""
        return self._cart_uuid

    @property
    def state(self):
        """State of the cart. Read-only. Use update_state or set_state to change."""
        return self._cart_state

    @property
    def sub_total(self):
        """Current sub_total, calculated from lineitems."""
        return sum([li.sub_total or 0 for li in self.lineitems])

    @property
    def total(self):
        """Current total, calculated from lineitems."""
        return self.sub_total + (self.tax or 0) + (self.shipping or 0)

    def adjust_expiration(self, newdate):
        """
        DEVELOPMENT ONLY: Adjust subscription end date.

        * Dev only because it doesn't actually change when Google or PP
          will bill the subscription next.
        """
        if hiicart_settings["LIVE"]:
            raise HiiCartError("Development only functionality.")
        if self.state != "PENDCANCEL" and self.state != "RECURRING":
            return
        curr_expiration = self.get_expiration()
        latest_pmnt = self.payments.order_by("-created")[0].created
        delta = curr_expiration - latest_pmnt
        newpmnt = newdate - delta
        for p in self.payments.all():
            if p.created > newpmnt:
                p.created = newpmnt
                p.save()

    def cancel_if_expired(self, grace_period=None):
        """Mark this cart as cancelled if recurring lineitems have expired."""
        if self.state != "PENDCANCEL" and self.state != "RECURRING":
            return
        if all([r.is_expired(grace_period) for r in self.recurring_lineitems]):
            self.set_state("CANCELLED")

    def cancel_recurring(self, skip_pendcancel=False):
        """
        Cancel any recurring items in the cart.

        skip_pendcancel skips the pending cancellation state and marks
        the cart as cancelled.
        """
        gateway = self.get_gateway()
        response = gateway.cancel_recurring(self)
        if skip_pendcancel:
            self.set_state("CANCELLED")
        self.update_state()
        return response

    def charge_recurring(self, grace_period=None):
        """
        Charge recurring purchases if necessary.

        Charges recurring items with the gateway, if possible. An optional
        grace period can be provided to avoid premature charging. This is
        provided since the gateway might be in another timezone, causing
        a mismatch between when an account can be charged.
        """
        gateway = self.get_gateway()
        gateway.charge_recurring(self, grace_period)
        self.update_state()

    def clone(self):
        """Clone this cart in the OPEN state."""
        dupe = copy.copy(self)
        # This method only works when id and pk have been cleared
        dupe.pk = None
        dupe.id = None
        dupe.set_state("OPEN", validate=False)
        dupe.gateway = None
        # Clear out any gateway-specific actions that might've been taken
        gateway = self.get_gateway()
        if gateway is not None:
            gateway.sanitize_clone(dupe)
        # Need to save before we can attach lineitems
        dupe.save()
        for item in self.lineitems:
            item.clone(dupe)
        return dupe

    def get_expiration(self):
        """Get expiration of recurring item or None if there are no recurring items."""
        return max([r.get_expiration() for r in self.recurring_lineitems])

    def get_gateway(self):
        """Get the PaymentGateway associated with this cart or None if cart has not been submitted yet.."""
        if self.gateway is None:
            return None
        return self._get_gateway(self.gateway)

    def _get_gateway(self, name):
        # importing now prevents circular import issues.
        from hiicart.gateway.amazon.gateway import AmazonGateway
        from hiicart.gateway.comp.gateway import CompGateway
        from hiicart.gateway.google.gateway import GoogleGateway
        from hiicart.gateway.paypal.gateway import PaypalGateway
        from hiicart.gateway.paypal2.gateway import Paypal2Gateway
        from hiicart.gateway.paypal_adaptive.gateway import PaypalAPGateway

        """Factory to get payment gateways."""
        if name == "amazon":
            return AmazonGateway(self)
        elif name == "comp":
            return CompGateway(self)
        elif name == "google":
            return GoogleGateway(self)
        elif name == "paypal":
            return PaypalGateway(self)
        elif name == "paypal2":
            return Paypal2Gateway(self)
        elif name == "paypal_adaptive":
            return PaypalAPGateway(self)
        else:
            raise HiiCartError("Unknown gateway: %s" % name)

    def save(self, *args, **kwargs):
        """Override to recalculate total and signal on state change."""
        self._recalc()
        if not self._cart_uuid:
            self._cart_uuid = str(uuid.uuid4())
        super(HiiCart, self).save(*args, **kwargs)
        # Signal sent after save in case someone queries database
        if self.state != self._old_state:
            cart_state_changed.send(sender="hiicart", cart=self,
                                    old_state=self._old_state,
                                    new_state=self.state)
            self._old_state = self.state

    def set_state(self, newstate, validate=True):
        """Set state of the cart, optionally not validating the transition."""
        if newstate == self.state:
            return
        if validate and not self._is_valid_transition(self.state, newstate):
            raise HiiCartError("Invalid state transition %s -> %s" % (
                               self.state, newstate))
        self._cart_state = newstate
        self.save()

    def submit(self, gateway_name, collect_address=False):
        """Submit this cart to a payment gateway."""
        gateway = self._get_gateway(gateway_name)
        self.gateway = gateway_name
        self.set_state("SUBMITTED")
        return gateway.submit(self, collect_address)

    def update_state(self):
        """
        Update cart state based on payments and lineitem expirations.

        Valid state transitions are listed in VALID_TRANSITIONS. This
        function contains the logic for when those various states are used.
        """
        newstate = None
        total_paid = sum([p.amount for p in self.payments.filter(state="PAID")])
        # Subscriptions involve multiple payments, therefore diff may be < 0
        if self.total - total_paid <= 0:
            newstate = "PAID"
        if any([li.is_active for li in self.recurring_lineitems]):
            newstate = "RECURRING"
        elif len(self.recurring_lineitems) > 0:
            # Paid and then cancelled, but not expired
            if newstate == "PAID" and not all([r.is_expired() for r in self.recurring_lineitems]):
                newstate = "PENDCANCEL"
            # Could be cancelled manually (is_active set to False)
            # Could be a re-subscription, but is now cancelled. Is not paid.
            # Could be expired
            elif newstate == "PAID" or self.state == "RECURRING":
                newstate = "CANCELLED"
        # Validate transition then save
        if newstate and newstate != self.state and self._is_valid_transition(self.state, newstate):
            self._cart_state = newstate
            self.save()


class LineItemBase(models.Model):
    """
    Abstract Base Class for a single line item in a purchase.

    An abstract base class is used here because of limitations in how
    inheritance in django works. If LineItem was created with a ForeignKey to
    cart and RecurringLineItem was subclassed, then cart.lineitems.all()
    would always return a list of LineItem, NOT a list of LineItem and
    RecurringLineItem. Therefore, we share common implementation details
    through the base class.
    http://stackoverflow.com/questions/313054/django-admin-interface-does-not-use-subclasss-unicode
    """
    _sub_total = DecimalField("Sub total", max_digits=18, decimal_places=10)
    _total = DecimalField("Total", max_digits=18, decimal_places=2, default=Decimal("0.00"))
    cart = models.ForeignKey(HiiCart, verbose_name="Cart")
    description = models.TextField("Description", blank=True)
    discount = DecimalField("Item discount", max_digits=18, decimal_places=10, default=Decimal("0.00"))
    name = models.CharField("Item", max_length=100)
    notes = generic.GenericRelation("Note")
    ordering = models.PositiveIntegerField("Ordering", default=0)
    quantity = models.PositiveIntegerField("Quantity")
    sku = models.CharField("SKU", max_length=255, default="1", db_index=True)
    thankyou = models.CharField("Thank you message.", max_length=255)

    class Meta:
        abstract = True
        ordering = ("ordering",)

    def __unicode__(self):
        return "%s - %d" % (self.name, self.total)

    def _recalc(self):
        """Recalculate totals"""
        self._sub_total = self.sub_total
        self._total = self.total

    def clone(self, newcart):
        """Clone this cart in the OPEN state."""
        dupe = copy.copy(self)
        # This method only works when id and pk have been cleared
        dupe.pk = None
        dupe.id = None
        dupe.cart = newcart
        dupe.save()
        return dupe

    def save(self, *args, **kwargs):
        """Override save to recalc before saving."""
        self._recalc()
        super(LineItemBase, self).save(*args, **kwargs)

    @property
    def sub_total(self):
        raise NotImplementedError()

    @property
    def total(self):
        raise NotImplementedError()


class OneTimeLineItemBase(LineItemBase):
    """Base class for line items that do not recur, for external apps to inherit"""

    unit_price = DecimalField("Unit price", max_digits=18, decimal_places=10)

    class Meta:
        abstract = True

    @property
    def sub_total(self):
        """Subtotal, calculated as price * quantity."""
        return self.quantity * self.unit_price

    @property
    def total(self):
        """Total, calculated as sub_total - discount."""
        return self.sub_total - self.discount


@HiiCart.register_lineitem_type()
class LineItem(OneTimeLineItemBase):
    """A single line item in a purchase."""
    pass


class Note(models.Model):
    """General note that can be attached to a cart, lineitem, or payment."""
    content_object = generic.GenericForeignKey()
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    text = models.TextField("Note")

    def __unicode__(self):
        return self.text


class Payment(models.Model):
    amount = DecimalField("amount", max_digits=18, decimal_places=2)
    cart = models.ForeignKey(HiiCart, related_name="payments")
    gateway = models.CharField("Payment Gateway", max_length=25, blank=True)
    notes = generic.GenericRelation("Note")
    state = models.CharField(max_length=16, choices=PAYMENT_STATES)
    created = models.DateTimeField("Created", auto_now_add=True)
    last_updated = models.DateTimeField("Last Updated", auto_now=True)
    transaction_id = models.CharField("Transaction ID", max_length=45, db_index=True, blank=True, null=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __init__(self, *args, **kwargs):
        """Override in order to keep track of changes to state."""
        super(Payment, self).__init__(*args, **kwargs)
        self._old_state = self.state

    def __unicode__(self):
        if self.id is not None:
            return u"#%i $%s %s %s" % (self.id, self.amount,
                                       self.state, self.created)
        else:
            return u"(unsaved) $%s %s" % (self.amount, self.state)

    def save(self, *args, **kwargs):
        super(Payment, self).save(*args, **kwargs)
        # Signal sent after save in case someone queries database
        if self.state != self._old_state:
            payment_state_changed.send(sender="hiicart", payment=self,
                                       old_state=self._old_state,
                                       new_state=self.state)
            self._old_state = self.state


class RecurringLineItemBase(LineItemBase):
    """Base class for line items that recur, for external apps to inherit from"""

    duration = models.PositiveIntegerField("Duration", help_text="Length of each billing cycle", null=True, blank=True)
    duration_unit = models.CharField("Duration Unit", max_length=5, choices=SUBSCRIPTION_UNITS, default="DAY", null=False)
    is_active = models.BooleanField("Is Currently Subscribed", default=False, db_index=True)
    payment_token = models.CharField("Recurring Payment Token", max_length=256, null=True)
    recurring_price = DecimalField("Recurring Price", default=Decimal("0.00"), max_digits=18, decimal_places=2)
    recurring_shipping = DecimalField("Recurring Shipping Price", default=Decimal("0.00"), max_digits=18, decimal_places=2)
    recurring_times = models.PositiveIntegerField("Recurring Times", help_text="Number of payments which will occur at the regular rate.  (optional)", default=0)
    recurring_start = models.DateTimeField(null=True, blank=True) # Allows delayed start to subscription.
    trial = models.BooleanField("Trial?", default=False)
    trial_price = DecimalField("Trial Price", default=Decimal("0.00"), max_digits=18, decimal_places=2)
    trial_length = models.PositiveIntegerField("Trial length", default=0)
    trial_times = models.PositiveIntegerField("Trial Times", help_text="Number of trial cycles", default=1)

    class Meta:
        abstract = True

    @property
    def sub_total(self):
        """Subtotal, calculated as price * quantity."""
        return self.quantity * self.recurring_price

    @property
    def total(self):
        """Total, calculated as sub_total - discount + shipping."""
        return self.sub_total - self.discount + self.recurring_shipping

    def get_expiration(self):
        """Expiration/next billing date for item."""
        delta = None
        if self.duration_unit == "DAY":
            delta = relativedelta(days=self.duration)
        elif self.duration_unit == "MONTH":
            delta = relativedelta(months=self.duration)
        payments = self.cart.payments.filter(
                state="PAID", amount__gt=0).order_by("-created")
        if not payments:
            if self.recurring_start:
                last_payment = self.recurring_start - delta
            else:
                return datetime.min
        else:
            last_payment = payments[0].created
        return last_payment + delta

    def is_expired(self, grace_period=None):
        """Get subscription expiration based on last payment optionally providing a grace period."""
        if grace_period:
            return datetime.now() > self.get_expiration() + grace_period
        elif hiicart_settings["EXPIRATION_GRACE_PERIOD"]:
            return datetime.now() > self.get_expiration() + hiicart_settings["EXPIRATION_GRACE_PERIOD"]


@HiiCart.register_lineitem_type(recurring=True)
class RecurringLineItem(RecurringLineItemBase):
    """
    Extra information needed for a recurring item, such as a subscription.

    To make a trial, put the trial price, tax, etc. into the parent LineItem,
    and mark this object trial=True, trial_length=xxx
    """
    pass
