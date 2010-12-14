import base

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User

from hiicart.models import HiiCart, LineItem, RecurringLineItem

class CompTestCase(base.HiiCartTestCase):
    """Tests for COMP payment gateway."""

    def test_submit(self):
        """Test submitting to COMP payment gateway."""
        self.assertEqual(self.cart.state, "OPEN")
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "PAID")

    def test_submit_recurring(self):
        """Test submitting to COMP payment gateway."""
        settings.HIICART_SETTINGS["COMP"]["ALLOW_RECURRING_COMP"] = True
        self.assertEqual(self.cart.state, "OPEN")
        self._add_recurring_item()
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "RECURRING")

    def test_submit_recurring_norecur(self):
        """Test submitting a recurring item with ALLOW_RECURRING_COMP = False"""
        settings.HIICART_SETTINGS["COMP"]["ALLOW_RECURRING_COMP"] =False 
        self.assertEqual(self.cart.state, "OPEN")
        self._add_recurring_item()
        result = self.cart.submit("comp")
        self.assertEqual(result, None)
        self.assertEqual(self.cart.state, "PENDCANCEL")

    def test_cancel_recurring(self):
        """Test cancelling a a comped purchase"""
        self.test_submit_recurring()
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_recurring()
        self.assertEqual(self.cart.state, "PENDCANCEL")

    def test_cancel_recurring_skip_pendcancel(self):
        """Test cancelling a a comped purchase (use skip_pendcancel=True)"""
        self.test_submit_recurring()
        self.assertEqual(self.cart.state, "RECURRING")
        self.cart.cancel_recurring(skip_pendcancel=True)
        self.assertEqual(self.cart.state, "CANCELLED")

    def test_charge_recurring(self):
        """
        Test charge recurring with and without grace period.
        
        NOTE: The timedelta used to adjust the expireation is never the same
              as grace_period because there will be a slight mismatch of a
              few milliseconds where the adjusted expiration will still
              fall outside the grace period.
        """
        cart_base = self.cart.clone()
        self.test_submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.payments.count(), 1)
        self.cart.charge_recurring()
        self.assertEqual(self.cart.payments.count(), 2)
        # With grace period 
        self.cart = cart_base.clone()
        self.test_submit_recurring()
        self.cart.adjust_expiration(datetime.now()-timedelta(days=1))
        self.assertEqual(self.cart.payments.count(), 1)
        self.cart.charge_recurring(grace_period=timedelta(days=2))
        self.assertEqual(self.cart.payments.count(), 1)
        self.cart.adjust_expiration(datetime.now()-timedelta(days=7))
        self.cart.charge_recurring(grace_period=timedelta(days=2))
        self.assertEqual(self.cart.payments.count(), 2)
