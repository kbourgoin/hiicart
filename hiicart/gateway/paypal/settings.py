"""Settings for Paypal gateway

**Required Settings:**
 * *BUSINESS* -- Seller's email address

**Required Settings when ENCRYPT set to True:***
 * *PUBLIC_KEY* -- Path to seller's public key file
 * *PRIVATE_KEY* -- Path to seller's private key file
 * *PUBLIC_CERT_ID* -- Public Cert Id provided by Paypal to public/private pair

**Optional Settings:**
 * *CURRENCY_CODE* -- Currency for transactions. [default: USD] 
 * *RETURN_ADDRESS* -- Return URL user is sent after a successful transaction.
            [default: None (uses acct default)] 
 * *LOCALE* -- Seller's Locale. [default: US]
 * *REATTEMPT* -- Re-attempt a failed recurring payment. [default: True]
 * *ENCRYPT* -- Encrypt generated button code. [default: False]
 * *IPN_URL* -- URL to send IPN messages. [default: None (uses acct defaults)]

"""
SETTINGS = { 
    "CURRENCY_CODE" : "USD",
    "RETURN_ADDRESS" : None,
    "LOCALE" : "US",
    "REATTEMPT" : True,
    "ENCRYPT" : False,
    "IPN_URL" : "",
    }
