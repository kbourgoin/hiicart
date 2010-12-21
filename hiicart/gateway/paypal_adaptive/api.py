"""Common functions to make calls to Paypal's Adaptive Payment API."""

import httplib2
import simplejson
import urllib
import urllib2

LIVE_ENDPOINT = "https://svcs.paypal.com/AdaptivePayments/%s"
SANDBOX_ENDPOINT = "https://svcs.sandbox.paypal.com/AdaptivePayments/%s"

def _endpoint_url(settings):
    if settings["LIVE"]:
        return LIVE_ENDPOINT
    else:
        return SANDBOX_ENDPOINT

def _send_command(settings, operation, params):
    """Send a command to the Adaptive API."""
    http = httplib2.Http()
    headers = {"X-PAYPAL-SECURITY-USERID": settings["USERID"],
               "X-PAYPAL-SECURITY-PASSWORD": settings["PASSWORD"],
               "X-PAYPAL-SECURITY-SIGNATURE": settings["SIGNATURE"],
               "X-PAYPAL-REQUEST-DATA-FORMAT": "NV",
               "X-PAYPAL-RESPONSE-DATA-FORMAT": "JSON",
               "X-PAYPAL-APPLICATION-ID": settings["APP_ID"],
               }
    params["requestEnvelope.errorLanguage"] = "en_US"
    # Yup, these have to be sorted. Why? Who the hell knows. Stupid Paypal.
    # There's no signature on the request that needs a common base string and
    # this sorting is only required with multiple receivers or Paypal returns
    # a 500 error with no help text.  Stupid.
    keys = params.keys()
    keys.sort()
    pairs = [(k,params[k]) for k in keys]
    response, data = http.request(_endpoint_url(settings) % operation, "POST",
                                  urllib.urlencode(pairs), headers=headers)
    return simplejson.loads(data)
