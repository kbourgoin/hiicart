"""Settings for Paypal2 gateway

**Required Settings:**
 * *PASSWORD* -- Paypal account API password (not account password)
 * *SELLER_EMAIL* -- Seller's email address
 * *SIGNATURE* -- Paypal API signature.
 * *USERID* -- Paypal account username. Note: this is NOT the account
            email address. This is the username used for API access.

**Optional Settings:**
 * *BASE_URL* -- Base URL used when generating IPN url. [default: None]
 * *CANCEL_URL* -- URL to redirect users to if they cancel out. [default: None]
 * *IPN_URL* -- URL to send IPN messages. [default: None]
 * *RETURN_URL* -- URL to redirect users after authorization is
            completed. [default: None]

**Note about [BASE|IPN]_URL**

Paypal2 can use a static IPN url, generate one using reverse()
or use the account settings default, through IPN_URL and BASE_URL.
If both IPN_URL and BASE_URL are defined, BASE_URL is ignored. If both
are set to None, Paypal will use the settings in the Paypal account.


"""
SETTINGS = { 
    'BASE_URL': None,
    'CANCEL_URL': None,
    'IPN_URL': None,
    'RETURN_URL': None,
    }
