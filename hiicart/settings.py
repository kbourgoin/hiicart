"""Settings for HiiCart

General settings for HiiCart. Gateway settings are in each gateway's module.

**Required Settings:**
 * *test* -- some test crap

**Optional Settings:**
 * *CART_SETTINGS_FN* -- Function providing cart-specific settings. Useful for
            injecting cart-specific gateway credentials.
            (e.g. cart x is processed by user y's Paypal account)
* *KEEP_ON_USER_DELETE* -- If True, stop CASCADE ON DELETE when User 
            is deleted. (django > 1.3 ONLY)
* *CHARGE_RECURRING_GRACE_PERIOD* -- Grace period before 
"""

# Default Settings
import os
import logging
from datetime import timedelta

SETTINGS = {
    'CART_COMPLETE':                    '/', 
    'CART_SETTINGS_FN':                 'apps.storefront.models.cart_settings',
    'KEEP_ON_USER_DELETE':              True,
    'CHARGE_RECURRING_GRACE_PERIOD':    timedelta(hours=12), # Delay before charging recurring item (good for avoid timezone issues)
    'EXPIRATION_GRACE_PERIOD':          timedelta(days=7), # Grace period to go without payment before deciding a subscription has expired
    'LIVE':                             False,
    'LOG':                              'hiicart.log',
    'LOG_LEVEL':                        logging.DEBUG,
    }

# Integrate django settings
from django.conf import settings as django_settings
SETTINGS.update(django_settings)
