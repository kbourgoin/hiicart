# TODO: Replace with class to manage/validate settings

default_settings = { 
             "BUSINESS" : "", #required, your paypal email address
             "CURRENCY_CODE" : "USD", # Currency code for Paypal transactions.
             "RETURN_ADDRESS" : None, # Url where user will be returned after a successful purchase
             "SSL" : False,
             "LOCALE" : "US",
             "REATTEMPT" : True,  # Reattempt on fail
             "LABEL" : "PayPal",
             "EXTRA_LOGGING" : False,
             "ENCRYPT" : False,
             # Path to the public key from PayPal, get this at: 
             # https://www.paypal.com/us/cgi-bin/webscr?cmd=_profile-website-cert"
             "PAYPAL_PUBKEY" : "",
             # Path to your paypal private key
             "PRIVATE_KEY": "",
             # Path to your paypal public key
             "PUBLIC_KEY" : "",
             # Your Cert ID, copied from the PayPal website after uploading your public key
             "PUBLIC_CERT_ID" : "",
             # Alternative to using Sites to look up current domain
             "IPN_URL" : "",
             "BUY_BUTTON_URL" : "http://images.paypal.com/images/x-click-but01.gif",
             "SUBSCRIBE_BUTTON_URL" : "https://www.paypal.com/en_US/i/btn/btn_subscribeCC_LG.gif",
             "UNSUBSCRIBE_BUTTON_URL" : "https://www.paypal.com/en_US/i/btn/btn_unsubscribe_LG.gif",
             "TEST_BUY_BUTTON_URL" : "https://www.sandbox.paypal.com/en_US/i/btn/btn_buynowCC_LG.gif",
             "TEST_SUBSCRIBE_BUTTON_URL" : "https://www.sandbox.paypal.com/en_US/i/btn/btn_subscribeCC_LG.gif",
             "TEST_UNSUBSCRIBE_BUTTON_URL" : "https://www.sandbox.paypal.com/en_US/i/btn/btn_unsubscribe_LG.gif"}
