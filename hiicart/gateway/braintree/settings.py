"""Settings for Braintree gateway

**Required Settings:**
 * *MERCHANT_ID* -- Merchant ID found in My User -> API Keys.
 * *MERCHANT_PUBLIC_KEY* -- Merchant Public Key found in My User -> API Keys.
 * *MERCHANT_PRVIATE_KEY* -- Merchant Private Key found in My User -> API Keys.

**Optional Settings:**
 * *CURRENCY* -- Currency code for transaction. [default: USD]
"""

SETTINGS = {
    "CURRENCY": "USD",
    }
