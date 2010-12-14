import base

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User

from hiicart.models import HiiCart, LineItem, RecurringLineItem

class PaypalTestCase(base.HiiCartTestCase):
    """Paypal related tests"""
    pass
