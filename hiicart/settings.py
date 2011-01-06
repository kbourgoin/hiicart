"""Settings for HiiCart

General settings for HiiCart. Gateway settings are in each gateway's module.

**Required Settings:**
 None.

**Optional Settings:**
 * *CART_COMPLETE* -- Where to send users after the gateway. [default: None]
 * *CART_SETTINGS_FN* -- Function to call to get cart-specific settings. See
            note below about how these work. [default: None]
 * *CHARGE_RECURRING_GRACE_PERIOD* -- Timedela for grace period before charging
            recurring items. Useful to inject a slight delay so that the billing
            attempt isn't made before the gateway allows it. [default: None]
 * *EXPIRATION_GRACE_PERIOD* -- Timedelta for grace period before a recurring
            item is marked as expired.  Useful because sometimes a eCheck needs
            to clear or the gateway is a day late with the recurring payment.
            [default: None]
 * *KEEP_ON_USER_DELETE* -- If True, stop CASCADE ON DELETE when associted User
            is deleted. (django > 1.3 ONLY)
 * *LIVE* -- If True, go against live gateway servers. [default: False]
 * *LOG* -- Logfile for HiiCart. [default: None]
 * *LOG_LEVEL* -- Logging level for the HiiCart log. [default: logging.DEBUG]


** About Global Settings**

Settings are read from global django settings as HIICART_SETTINGS.  This should
contain both library-wide and gateway-specific settings.  For example:

HIICART_SETTINGS = {
    "LOG": "hiicart.log",
    "GOOGLE": {
        "MERCHANT_ID": "foo",
        "MERCHANT_KEY": "bar",
        }
    }

**About Cart-Speficic Settings**

Due to the need to run a storefront with multiple sellers (e.g. goodsie.com)
this library supports overriding global settings for any operation using
cart-speficic settings.  To use this, set CART_SETTINGS_FN to the name of a
function that returns a settings dict for any cart passed to it.  This dict
should contain any gateway-specific settings (key, pass, etc.) to be used
only for that cart.
"""

import logging

SETTINGS = {
    'CART_COMPLETE': None,
    'CART_SETTINGS_FN': None,
    'CHARGE_RECURRING_GRACE_PERIOD': None,
    'EXPIRATION_GRACE_PERIOD': None,
    'KEEP_ON_USER_DELETE': None,
    'LIVE': False,
    'LOG': 'hiicart.log',
    'LOG_LEVEL': logging.DEBUG,
    }

# Integrate django settings
from django.conf import settings as django_settings
SETTINGS.update(django_settings.HIICART_SETTINGS)
