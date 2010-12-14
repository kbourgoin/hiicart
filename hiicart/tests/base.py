import unittest

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User

from hiicart.models import HiiCart, LineItem, RecurringLineItem

class HiiCartTestCase(unittest.TestCase):
    """Base class for HiiCart tests"""

    def setUp(self):
        self.test_user = User.objects.create(username="tester", email="foo@bar.com") 
        self.cart = HiiCart.objects.create(user=self.test_user)
        self.lineitem = LineItem.objects.create(cart=self.cart,name="Test Item",
                                                quantity=1, sku="1",
                                                unit_price=Decimal("1.99"),
                                                thankyou="Thank you")

    def tearDown(self):
        self.test_user.delete()
        self.cart.delete()

    def _add_recurring_item(self):
        """Add a RecurringLineItem to self.cart."""
        return RecurringLineItem.objects.create(cart=self.cart, name="Recurring",
                                                quantity=1, sku="42",
                                                duration=12, duration_unit="MONTH",
                                                recurring_price=Decimal("20.00"),
                                                thankyou="Thank you")
