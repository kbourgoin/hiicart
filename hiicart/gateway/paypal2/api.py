"""Functions to make calls to Paypal's NVP API."""
# TODO: Make this an object that gets its own settings (using _SharedBase?)

import httplib2
import urllib
import urllib2

from datetime import datetime
from decimal import Decimal
from django.core.urlresolvers import reverse
from urllib import unquote

LIVE_ENDPOINT = "https://api-3t.paypal.com/nvp"
SANDBOX_ENDPOINT = "https://api-3t.sandbox.paypal.com/nvp"

def _ipn_url(settings):
    if not settings["IPN_URL"]:
        if "BASE_URL" not in settings:
            raise GatewayError(
                    "Either IPN_URL or BASE_URL is required.")
        # Avoid circular import
        from hiicart.gateway.paypal2.views import ipn
        return "%s%s" % (settings["BASE_URL"], reverse(ipn))
    else:
        return settings["IPN_URL"]

def _send_command(params, settings):
    """Send a command to the NVP API."""
    params["VERSION"] = "64.4"
    params["USER"] = settings["USERID"]
    params["PWD"] = settings["PASSWORD"]
    params["SIGNATURE"] = settings["SIGNATURE"]
    keys = params.keys()
    keys.sort()
    pairs = [(k,params[k]) for k in keys]
    url = LIVE_ENDPOINT if settings["LIVE"] else SANDBOX_ENDPOINT
    response, data = httplib2.Http().request(url, "POST",
                                             urllib.urlencode(pairs))
    data = unquote(data)
    # TODO: logging
    return dict([(l,r) for l,r in [p.split('=') for p in data.split('&')]])

def create_recurring_profile(token, payer_id, cart, settings):
    """Call CreateRecurringPaymentsProfile for each recurringlineitem.
    NOTE: There's no way for an IPN url to be provided here.  All recurring
          profiles will use the account defaults."""
    # TODO: The above note about the IPN needs to be a BIG warning in the wiki
    # TODO: Trial Periods, Shipping (cost and address), Tax
    for item in cart.recurringlineitems.all():
        params = {"METHOD": "CreateRecurringPaymentsProfile",
                  "TOKEN": token,
                  "PROFILESTARTDATE": item.recurring_start or datetime.now(),
                  "PROFILEREFERENCE": cart._cart_uuid,
                  "DESC": item.description,
                  "BILLINGPERIOD": "Month", #item.duration_unit,
                  "BILLINGFREQUENCY": item.duration,
                  "AMT": item.recurring_price,
                  "CURRENCYCODE": "USD", # TODO: Make setting
                  "PAYERID": payer_id,
                  }
        result = _send_command(params, settings)
        if result.get("PROFILESTATUS", "") == "ActiveProfile":
            item.is_active = True
            item.payment_token = result["PROFILEID"]
            item.save()
    cart.update_state()

def do_express_payment(token, payer_id, cart, settings):
    """Call DoExpressCheckoutPayment for each lineitem."""
    params = {"METHOD": "DoExpressCheckoutPayment",
              "TOKEN": token,
              "PAYERID": payer_id,
              "PAYMENTREQUEST_0_CURRENCYCODE": "USD", # TODO: Make setting
              "PAYMENTREQUEST_0_ITEMAMT": cart.total.quantize(Decimal(".01")),
              "PAYMENTREQUEST_0_INVNUM": cart.cart_uuid,
              "PAYMENTREQUEST_0_MAXAMT": cart.total,
              "PAYMENTREQUEST_0_NOTIFYURL": _ipn_url(settings),
              "PAYMENTREQUEST_0_PAYMENTACTION": "Sale",
              "PAYMENTREQUEST_0_SELLERPAYPALACCOUNTID": settings["SELLER_EMAIL"],
              }
    params["PAYMENTREQUEST_0_AMT"] = cart.total.quantize(Decimal(".01"))
    for i, item in enumerate(cart.lineitems.all()):
        params["L_PAYMENTREQUEST_0_NAME%i"%i] = item.name
        params["L_PAYMENTREQUEST_0_DESC%i"%i] = item.description
        params["L_PAYMENTREQUEST_0_AMT%i"%i] = item.total.quantize(Decimal(".01"))
        params["L_PAYMENTREQUEST_0_NUMBER%i"] = item.sku
    result = _send_command(params, settings)
    if result.get("PAYMENTINFO_0_PAYMENTSTATUS", "") == "Completed":
        # TODO: This sucks. Consider changing IPNBase to APIBase so there's no ipn/api distincation in gateways
        from ipn import Paypal2IPN
        Paypal2IPN()._create_payment(cart, cart.total,
                                     result["PAYMENTINFO_0_TRANSACTIONID"],
                                     "PAID")
        cart.update_state()
    return result

def get_express_details(token, settings):
    """Use GetExpressCheckoutDetails to get information."""
    params = {"METHOD": "GetExpressCheckoutDetails",
              "TOKEN": token}
    # TODO: This should update cart info like other gateways
    return _send_command(params, settings) 

def set_express_checkout(cart, settings, collect_address=False):
    from hiicart.gateway.paypal2.views import authorized
    params = {"METHOD": "SetExpressCheckout",
              "CANCELURL": settings["CANCEL_URL"],
              "RETURNURL": settings["BASE_URL"] + reverse(authorized),
              "NOSHIPPING": "1", # No shipping support for now
              "PAYMENTREQUEST_0_CURRENCYCODE": "USD", # TODO: Make setting
              "PAYMENTREQUEST_0_ITEMAMT": cart.total.quantize(Decimal(".01")),
              "PAYMENTREQUEST_0_INVNUM": cart.cart_uuid,
              "PAYMENTREQUEST_0_MAXAMT": cart.total,
              "PAYMENTREQUEST_0_NOTIFYURL": _ipn_url(settings),
              "PAYMENTREQUEST_0_PAYMENTACTION": "Sale",
              "PAYMENTREQUEST_0_SELLERPAYPALACCOUNTID": settings["SELLER_EMAIL"],
            }
    if cart.lineitems.count() > 0:
        params["PAYMENTREQUEST_0_AMT"] = cart.total.quantize(Decimal(".01"))
        for i, item in enumerate(cart.lineitems.all()):
            params["L_PAYMENTREQUEST_0_NAME%i"%i] = item.name
            params["L_PAYMENTREQUEST_0_DESC%i"%i] = item.description
            params["L_PAYMENTREQUEST_0_AMT%i"%i] = item.total.quantize(Decimal(".01"))
            params["L_PAYMENTREQUEST_0_NUMBER%i"] = item.sku
    else:
        params["PAYMENTREQUEST_0_AMT"] = cart.total.quantize(Decimal(".01"))
        for i, item in enumerate(cart.recurringlineitems.all()):
            params["L_BILLINGTYPE%i"%i] = "RecurringPayments"
            params["L_BILLINGAGREEMENTDESCRIPTION%i"%i] = item.description
            #params["L_AMT%i"%i] = item.recurring_price.quantize(Decimal(".01"))
            #params["L_PAYMENTREQUEST_0_NAME%i"%i] = item.name
            #params["L_PAYMENTREQUEST_0_DESC%i"%i] = item.description
            params["L_PAYMENTREQUEST_0_AMT%i"%i] = item.total.quantize(Decimal(".01"))
            params["L_PAYMENTREQUEST_0_NUMBER%i"%i] = item.sku
    return _send_command(params, settings)
