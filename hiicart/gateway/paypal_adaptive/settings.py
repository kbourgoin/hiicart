"""Settings for Paypal's Adaptive Payments gateway

**Required Settings**
 * *APP_ID* -- Paypal App ID
 * *PASSWORD* -- Paypal account API password (not account password)
 * *RECEIVERS* -- Tuple containing information about each payment receiver.
           The format is (email, amount, is_primary_recipient) where amount
           is a Deimal. Currently, the only want to accomplish this is through
           cart-specific settings, since the amount is determined on a per
           cart basis. In the future, that should be changed to a percentage
           so that cart-specific settings aren't necessary.
 * *SIGNATURE* -- Paypal API signature.
 * *USERID* -- Paypal account username. Note: this is NOT the account
            email address. This is the username used for API access.

**Optional Settings**
 * *BASE_URL* -- Base URL to use when generating IPN URL. Ignored if
            using IPN_URL setting. [default: None]
 * *CANCEL_URL* -- URL to redirect user to if they cancel. [default: None]
 * *IPN_URL* -- Target URL for IPN messages. [default: None]
 * *RETURN_URL* -- URL to redirect user to after purchase. [default: None]
"""

SETTINGS = {
    "APP_ID": None,
    "BASE_URL": None,
    "CANCEL_URL": None,
    "IPN_URL": None,
    "PASSWORD": None,
    "RECEIVERS": [],
    "RETURN_URL": None,
    "SIGNATURE": None,
    "USERID": None,
}
