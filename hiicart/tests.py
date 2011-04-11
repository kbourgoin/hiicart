import unittest

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User

from hiicart.models import HiiCart, LineItem, RecurringLineItem

class HiiCartTestCase(unittest.TestCase):
    """Basic tests to ensure HiiCart is working."""
    def setUp(self):
        self.test_user = User.objects.create(username="tester", email="foo@bar.com")
        self.cart = HiiCart.objects.create(user=self.test_user)
        self.lineitem = LineItem.objects.create(cart=self.cart,name="Test Item",
                                                quantity=1, sku="1",
                                                unit_price=Decimal("1.99"))

    def tearDown(self):
        self.test_user.delete()
        self.cart.delete()

    def _add_recurring_item(self):
        """Add a RecurringLineItem to self.cart."""
        return RecurringLineItem.objects.create(cart=self.cart, name="Recurring",
                                                quantity=1, sku="42",
                                                duration=12, duration_unit="MONTH",
                                                recurring_price=Decimal("20.00"))

### HiiCart Tests

    def test_cart_create(self):
        """Test basic object creation and saving"""
        self.assertNotEqual(self.cart, None)
        self.assertNotEqual(self.lineitem, None)
        self.assertEqual(self.cart, self.lineitem.cart)

    def test_cart_clone(self):
        """Test cart cloning."""
        newcart = self.cart.clone()
        newcart.save()
        self.assertNotEqual(self.cart.id, newcart.id)
        newcart.delete()

    def test_lineitem_clone(self):
        """Test line item cloning."""
        newitem = self.lineitem.clone(self.cart)
        newitem.save()
        self.assertNotEqual(self.lineitem.id, newitem.id)
        newitem.delete()

    def test_cart_recalc(self):
        """
        Test the recalc functionality of HiiCart.
        Testing tax and shipping will come later, when we're using it.
        """
        self.assertEqual(self.cart.total, Decimal("1.99"))
        lineitem2 = LineItem.objects.create(cart=self.cart, name="Test 2",
                                            quantity=1, sku="2",
                                            unit_price=Decimal("5.00"))
        self.assertEqual(self.cart.total, Decimal("6.99"))
        lineitem2.delete()

    def test_lineitem_recalc(self):
        """
        Test the recalc functionality of LineItem and RecurringLineItem.
        Testing discount, tax and shipping will come later, when we're using it.
        """
        self.assertEqual(self.cart.total, Decimal("1.99"))
        lineitem2 = LineItem.objects.create(cart=self.cart, name="Test 2",
                                            quantity=1, sku="2",
                                            unit_price=Decimal("5.00"))
        self.assertEqual(self.cart.total, Decimal("6.99"))
        self.assertEqual(lineitem2.total, Decimal("5.00"))
        lineitem2.quantity = 2
        lineitem2.save()
        self.assertEqual(lineitem2.total, Decimal("10.00"))
        self.assertEqual(self.cart.total, Decimal("11.99"))
        lineitem2.delete()

    def test_get_expiration(self):
        """Test getting the expiration of a recurring item."""
        self.test_comp_submit_recurring()
        expiration = self.cart.get_expiration().date()
        self.assertEqual(expiration, date.today()+timedelta(days=365))

    def test_adjust_expiration(self):
        """Test adjusting the expiration of a recurring item."""
        self.test_comp_submit_recurring()
        newdate = datetime.now() + timedelta(days=120)
        self.cart.adjust_expiration(newdate)
        expiration = self.cart.get_expiration()
        self.assertEqual(expiration, newdate)

    def test_cancel_if_expired(self):
        """Test cancelling a cart when expired."""
        cart_base = self.cart.clone()
        # RECURRING -> CANCELLED
        self.test_comp_submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_if_expired()
        self.assertEqual(self.cart.state, "CANCELLED")
        # PENDCANCEL -> CANCELLED
        self.cart = cart_base.clone()
        self.test_comp_submit_recurring_norecur()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.state, "PENDCANCEL")
        self.cart.cancel_if_expired()
        self.assertEqual(self.cart.state, "CANCELLED")

    def test_cancel_if_expired_grace_period(self):
        """Test cancelling a cart when expired after a grace period."""
        cart_base = self.cart.clone()
        # RECURRING -> CANCELLED
        self.test_comp_submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_if_expired(grace_period=timedelta(days=7))
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.adjust_expiration(datetime.now()-timedelta(days=8))
        self.cart.cancel_if_expired(grace_period=timedelta(days=7))
        self.assertEqual(self.cart.state, "CANCELLED")
        # PENDCANCEL -> CANCELLED
        self.cart = cart_base.clone()
        self.test_comp_submit_recurring_norecur()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.state, "PENDCANCEL")
        self.cart.cancel_if_expired(grace_period=timedelta(days=7))
        self.assertEqual(self.cart.state, "PENDCANCEL")
        self.cart.adjust_expiration(datetime.now()-timedelta(days=8))
        self.cart.cancel_if_expired(grace_period=timedelta(days=7))
        self.assertEqual(self.cart.state, "CANCELLED")

    def test_notes(self):
        """Test attaching notes to things."""
        note = "this is a test note."
        self.test_comp_submit_recurring()
        # HiiCart
        self.cart.notes.create(text=note)
        self.assertEqual(self.cart.notes.count(), 1)
        self.assertEqual(self.cart.notes.all()[0].text, note)
        # LineItem
        li = self.cart.one_time_lineitems[0]
        li.notes.create(text=note)
        self.assertEqual(li.notes.count(), 1)
        self.assertEqual(li.notes.all()[0].text, note)
        # RecurringLineItem
        ri = self.cart.recurring_lineitems[0]
        ri.notes.create(text=note)
        self.assertEqual(ri.notes.count(), 1)
        self.assertEqual(ri.notes.all()[0].text, note)
        # Payment
        p = self.cart.payments.all()[0]
        p.notes.create(text=note)
        self.assertEqual(p.notes.count(), 1)
        self.assertEqual(p.notes.all()[0].text, note)

### Comp tests

    def test_comp_submit(self):
        """Test submitting to COMP payment gateway."""
        self.assertEqual(self.cart.state, "OPEN")
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "PAID")

    def test_comp_submit_recurring(self):
        """Test submitting to COMP payment gateway."""
        settings.HIICART_SETTINGS["COMP"]["ALLOW_RECURRING_COMP"] = True
        self.assertEqual(self.cart.state, "OPEN")
        self._add_recurring_item()
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "RECURRING")

    def test_comp_submit_recurring_norecur(self):
        """Test submitting a recurring item with ALLOW_RECURRING_COMP = False"""
        settings.HIICART_SETTINGS["COMP"]["ALLOW_RECURRING_COMP"] =False
        self.assertEqual(self.cart.state, "OPEN")
        self._add_recurring_item()
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "PENDCANCEL")

    def test_comp_cancel_recurring(self):
        """Test cancelling a a comped purchase"""
        self.test_comp_submit_recurring()
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_recurring()
        self.assertEqual(self.cart.state, "PENDCANCEL")

    def test_comp_cancel_recurring_skip_pendcancel(self):
        """Test cancelling a a comped purchase (use skip_pendcancel=True)"""
        self.test_comp_submit_recurring()
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_recurring(skip_pendcancel=True)
        self.assertEqual(self.cart.state, "CANCELLED")

    def test_comp_charge_recurring(self):
        """
        Test charge recurring with and without grace period.

        NOTE: The timedelta used to adjust the expireation is never the same
              as grace_period because there will be a slight mismatch of a
              few milliseconds where the adjusted expiration will still
              fall outside the grace period.
        """
        cart_base = self.cart.clone()
        self.test_comp_submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.payments.count(), 1)
        self.cart.charge_recurring()
        self.assertEqual(self.cart.payments.count(), 2)
        # With grace period
        self.cart = cart_base.clone()
        self.test_comp_submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.payments.count(), 1)
        self.cart.charge_recurring(grace_period=timedelta(days=2))
        self.assertEqual(self.cart.payments.count(), 1)
        self.cart.adjust_expiration(datetime.now()-timedelta(days=7))
        self.cart.charge_recurring(grace_period=timedelta(days=2))
        self.assertEqual(self.cart.payments.count(), 2)

### Google Checkout Tests

### PayPal Tests

### Amazon Payments Tests

