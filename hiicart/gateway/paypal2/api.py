"""Common functions to make calls to Paypal's Adaptive Payment API."""

import httplib2
import simplejson
import urllib
import urllib2

LIVE_ENDPOINT = "https://api-3t.paypal.com/nvp"
SANDBOX_ENDPOINT = "https://api-3t.sandbox.paypal.com/nvp"

def _endpoint_url(settings):
    if settings["LIVE"]:
        return LIVE_ENDPOINT
    else:
        return SANDBOX_ENDPOINT

def _send_command(settings, operation, params):
    """Send a command to the Adaptive API."""
    import pdb; pdb.set_trace()
    http = httplib2.Http()
    headers = {"X-PAYPAL-SECURITY-USERID": settings["USERID"],
               "X-PAYPAL-SECURITY-PASSWORD": settings["PASSWORD"],
               "X-PAYPAL-SECURITY-SIGNATURE": settings["SIGNATURE"],
               "X-PAYPAL-REQUEST-DATA-FORMAT": "NV",
               "X-PAYPAL-RESPONSE-DATA-FORMAT": "JSON",
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
