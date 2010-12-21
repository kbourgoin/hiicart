import logging
import os

from datetime import timedelta

# Django settings for example project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'exampledb',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@8dx$3bx9!25ul_sy!%tk$g_i88nmv4ksu=cd4=3l0o*#b1#6^'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'example.urls'

TEMPLATE_DIRS = (
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'south',
    'hiicart',
)

# HiiCart Settings
# TODO: Create goodsie2 test accounts
HIICART_SETTINGS = {
    'CART_COMPLETE':                    '/', 
    'CART_SETTINGS_FN':                 'apps.storefront.models.cart_settings',
    'CHARGE_RECURRING_GRACE_PERIOD':    timedelta(hours=12), # Delay before charging recurring item (good for avoid timezone issues)
    'EXPIRATION_GRACE_PERIOD':          timedelta(days=7), # Grace period to go without payment before deciding a subscription has expired
    'LIVE':                             False,
    'LOG':                              'hiicart.log',
    'LOG_LEVEL':                        logging.DEBUG,
    'COMP': {
        'ALLOW_RECURRING_COMP':         False
        },
    'GOOGLE': {
        'MERCHANT_ID':                  '',
        'MERCHANT_KEY':                 '',
        'IPN_AUTH_VALS':                'apps.storefront.models.google_auth',
        },
    'PAYPAL': {
        'BUSINESS':                     '',
        'ENCRYPT':                      False,
        'IPN_URL':                      'http://kfb.is-a-geek.net/hiicart/paypal/ipn/',
        'PAYPAL_PUBKEY':                os.path.abspath(os.path.join(os.path.dirname(__file__), "apps/payments/paypal.sandbox.pem")),
        },
    'PAYPAL_ADAPTIVE': {
        'USERID':                       'beta-a_1265578093_biz_api1.flavors.me',
        'PASSWORD':                     'HC8ANL8SMXBXCDD9',
        'SIGNATURE':                    'AtCXFEkc6iZWU9Da-95bPn-qQd5qANzzECohvcANgyuQhOIZoOumoM2O',
        'APP_ID':                       'APP-80W284485P519543T',
        },
    'AMAZON': {
        'AWS_KEY':                      '',
        'AWS_SECRET':                   '',
        'CBUI_RETURN_URL':              'http://beta.goodsie2.com/hiicart/amazon/cbui',
        'IPN_URL':                      'http://kfb.is-a-geek.net/hiicart/amazon/ipn',
        'BUYER_CANCEL_URL':             '/',
        'RETURN_URL':                   '/',
        'ERROR_RETURN_URL':             '/',
        'CANCEL_RETURN_URL':            '/'
        }
    }
