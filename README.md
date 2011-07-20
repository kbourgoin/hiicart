HiiCart - Django Shopping Cart
===============================

A simple shopping cart implementation with support for PayPal,
Google Checkout, Amazon Payments, and Braintree.


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
        return cart.submit("google")

This returns an object containing the redirect URL for you user.

Example App
-----------

An example app is included that shows very generally how to get everything set
up and working. Right now it really needs a lot of work, but is functional for
the most basic case.
