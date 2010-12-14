import urllib
import urllib2
import urlparse
import xml.etree.cElementTree as ET

from datetime import datetime, tzinfo
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.datastructures import SortedDict
from urllib2 import HTTPError

from hiicart.gateway.paypal_adaptive import fps
from hiicart.gateway.paypal_adaptive.errors import PaypalAdaptivePaymentsGatewayError
from hiicart.gateway.paypal_adaptive.settings import default_settings
from hiicart.gateway.base import IPNBase
from hiicart.models import HiiCart, Payment

class PaypalAdaptivePaymentsIPN(IPNBase):
    """Payment Gateway for Paypal Adaptive Payments."""

    def __init__(self):
        super(PaypalAdaptivePaymentsIPN, self).__init__(
                "paypal_adaptive", default_settings)
