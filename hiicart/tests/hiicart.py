import base

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User

from hiicart.models import HiiCart, LineItem, RecurringLineItem

class HiiCartTestCase(base.HiiCartTestCase):
    """Basic tests to ensure HiiCart is working."""

    def _submit_recurring(self):
        settings.HIICART_SETTINGS["COMP"]["ALLOW_RECURRING_COMP"] = True
        self.assertEqual(self.cart.state, "OPEN")
        self._add_recurring_item()
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "RECURRING")

    def _submit_recurring_norecur(self):
        settings.HIICART_SETTINGS["COMP"]["ALLOW_RECURRING_COMP"] =False 
        self.assertEqual(self.cart.state, "OPEN")
        self._add_recurring_item()
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "PENDCANCEL")

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
        self._submit_recurring()
        expiration = self.cart.get_expiration().date()
        self.assertEqual(expiration, date.today()+timedelta(days=365))

    def test_adjust_expiration(self):
        """Test adjusting the expiration of a recurring item."""
        self._submit_recurring()
        newdate = datetime.now() + timedelta(days=120)
        self.cart.adjust_expiration(newdate)
        expiration = self.cart.get_expiration()
        self.assertEqual(expiration.date(), newdate.date())

    def test_cancel_if_expired(self):
        """Test cancelling a cart when expired."""
        cart_base = self.cart.clone()
        # RECURRING -> CANCELLED
        self._submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_if_expired()
        self.assertEqual(self.cart.state, "CANCELLED")
        # PENDCANCEL -> CANCELLED
        self.cart = cart_base.clone()
        self._submit_recurring_norecur()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.state, "PENDCANCEL")
        self.cart.cancel_if_expired()
        self.assertEqual(self.cart.state, "CANCELLED")

    def test_cancel_if_expired_grace_period(self):
        """Test cancelling a cart when expired after a grace period."""
        cart_base = self.cart.clone()
        # RECURRING -> CANCELLED
        self._submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_if_expired(grace_period=timedelta(days=7))
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.adjust_expiration(datetime.now()-timedelta(days=8))
        self.cart.cancel_if_expired(grace_period=timedelta(days=7))
        self.assertEqual(self.cart.state, "CANCELLED")
        # PENDCANCEL -> CANCELLED
        self.cart = cart_base.clone()
        self._submit_recurring_norecur() 
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
        self._submit_recurring()
        # HiiCart
        self.cart.notes.create(text=note)
        self.assertEqual(self.cart.notes.count(), 1)
        self.assertEqual(self.cart.notes.all()[0].text, note)
        # LineItem
        li = self.cart.lineitems.all()[0]
        li.notes.create(text=note)
        self.assertEqual(li.notes.count(), 1)
        self.assertEqual(li.notes.all()[0].text, note)
        # RecurringLineItem
        ri = self.cart.recurringlineitems.all()[0]
        ri.notes.create(text=note)
        self.assertEqual(ri.notes.count(), 1)
        self.assertEqual(ri.notes.all()[0].text, note)
        # Payment
        p = self.cart.payments.all()[0]
        p.notes.create(text=note)
        self.assertEqual(p.notes.count(), 1)
        self.assertEqual(p.notes.all()[0].text, note)

    def test_state_transitions(self):
        """Test all possible and impossible state transitions."""
        pass


