"""Support for Amazon's Flexible Payment System (FPS)"""

import base64
import hashlib
import hmac
import logging
import urllib
import urllib2
import urlparse
import xml.etree.cElementTree as ET

from datetime import datetime, tzinfo
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.http import urlencode
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from urllib2 import HTTPError

from hiicart.gateway.base import PaymentGatewayBase, CancelResult, SubmitResult

LIVE_FPS_URL = "https://fps.amazonaws.com/"
TEST_FPS_URL = "https://fps.sandbox.amazonaws.com/"

def _fps_base_url(settings):
    if settings['LIVE']:
        url = mark_safe(LIVE_FPS_URL)
    else:
        url = mark_safe(TEST_FPS_URL)
    return url

def do_fps(action, method, settings, **params):
    """Make a request against the FPS api."""
    values = {"AWSAccessKeyId" : settings["AWS_KEY"],
              "SignatureMethod" : "HmacSHA256",
              "SignatureVersion" : 2,
              "Timestamp" : datetime.utcnow().isoformat() + '-00:00', 
              "Version" : "2008-09-17",
              "Action" : action}
    values.update(params)
    values["Signature"] = generate_signature(method, values, 
                                             _fps_base_url(settings), settings)
    url = "%s?%s" % (_fps_base_url(settings), urllib.urlencode(values))
    request = urllib2.Request(url)
    #request.add_header("Content-type", "application/x-www-form-urlencoded")
    try:
        req = urllib2.urlopen(request)
        response = req.read()
        #response = urllib2.urlopen(request).read()
    except HTTPError, e:
        if e.code == 400:
            response = e.read()
        else:
            raise
    return response

def generate_signature(verb, values, request_url, settings):
    """
    Generate signature for call. (same signature is used for CBUI call)


    NOTE: Python's urlencode doesn't work for Amazon. Spaces need to be %20
          and not +. This only affects the signature generation, not the
          key/values submitted.
    """
    keys = values.keys()
    keys.sort()
    sorted = SortedDict([(k, values[k]) for k in keys])
    query = urllib.urlencode(sorted)
    query = query.replace("+", "%20")
    parsed = urlparse.urlsplit(request_url)
    base = "%(verb)s\n%(hostheader)s\n%(requesturi)s\n%(query)s" % {
           "verb" : verb.upper(),
           "hostheader" : parsed.hostname.lower(),
           "requesturi" : parsed.path,
           "query" : query}
    s = hmac.new(str(settings["AWS_SECRET"]),  base, hashlib.sha256)
    return base64.encodestring(s.digest())[:-1]
