HiiCart  -- Django Shopping Cart
================================

A simple shopping cart implementation with support for PayPal,
Google Checkout, and Amazon Payments.


Installation and Setup
----------------------

Installation is as easy as installing with easy_install or pip and
adding the appropriate settings for the gateways you want to use.  Please see
the documentation in hiicart/settings.py for more details about the settings
available.

Once set up, create LineItem and HiiCart objects to submit payments:

    def foo():
    cart = HiiCart.objects.create() 
    LineItem.objects.create(
        cart=cart, description="foo", name="bar",
        quantity=1, sku="12345", thankyou="thanks!",
        unit_price=9.99)
    return c.submit("google")

This returns an object containing the redirect URL for you user.
