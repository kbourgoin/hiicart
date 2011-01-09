"""Settings for Google Checkout gateway

**Required Settings:**
 * *MERCHANT_ID* -- Merchant ID found in Settings -> Integration in Checkout.
 * *MERCHANT_KEY* -- Merchant Key found in Settings -> Integration in Checkout.

**Optional Settings:**
 * *CURRENCY* -- Currency code for transaction. [default: USD]
 * *IPN_AUTH_VALS* -- Function to retrieve BASIC Auth strings used to validate
            Checkout's IPN calls. Checkout uses BASIC Auth when sending IPN
            messages using the merchant id/key as login/pass. This function
            should return an enumerable of the base64 encoded strings.
            ex: set(map(lambda x: b64encode("%s:%s" % (id, key))), keyset)
            This is useful when hosting a storefront that uses multiple
            Checkout accounts and MERCHANT_ID/MERCHANT_KEY aren't sufficient.
            [default: None]
"""

SETTINGS = {
    "CURRENCY": "USD",
    "IPN_AUTH_VALS": None,
    }
