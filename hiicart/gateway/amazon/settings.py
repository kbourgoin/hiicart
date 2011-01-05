"""Settings for Amazon Payments gateway

**Required Settings**
 * *AWS_KEY* -- Amazon Web Services key
 * *AWS_SECRET* -- Amazon Web Services secret

**Optional Settings**
 * *ACCEPT_CC* -- If true, accept credit cart payments. [default: True]
 * *ACCEPT_ACH* -- Accept ACH (bank transfer) payments. [default: True]
 * *ACCEPT_ABT* -- Accept Amazon balance transfer payments. [default: True]
 * *CANCEL_RETURN_URL* -- URL to redirect user when cancelling. [default: None]
 * *CBUI_LOGO_URL* -- URL of logo image to use in co-branded ui. [default: None]
 * *CBUI_RETURN_URL* -- Return URL for user after authorizing in the
            co-branded ui. [default: None]
 * *CBUI_WEBSITE_DESC* -- Website description to display in the co-branded
            ui. [default: None]
 * *ERROR_RETURN_URL* -- URL to redirect user to on error. [default: None]
 * *IPN_URL* -- URL to receive IPN messages. [default: None (uses acct setting)]
 * *RETURN_URL* -- URL to redirect user to if they want to return
            to the store. [default: None]
"""

SETTINGS = {
    "ACCEPT_CC" : True,
    "ACCEPT_ACH" : True,
    "ACCEPT_ABT" : True
    "AWS_KEY" : None,
    "AWS_SECRET" : None,
    "CANCEL_RETURN_URL": None, 
    "CBUI_LOGO_URL" : None,
    "CBUI_RETURN_URL" : None,
    "CBUI_WEBSITE_DESC" : None,
    "ERROR_RETURN_URL": None,
    "IPN_URL": None,
    "RETURN_URL": None,
    }
