from setuptools import setup, find_packages
from hiicart import __version__ as version


# Also requires python-dev and python-openssl
setup(

    name = "HiiCart",

    version = version,

    packages = find_packages(),

    install_requires = ['python-dateutil>=1.4,<2.0.0', 'simplejson>=2.1.3', 'braintree>=2.10.0'],
    include_package_data = True,

    # metadata for upload to PyPI
    author = "Keith Bourgoin",
    author_email = "keith.bourgoin@gmail.com",
    description = "HiiDef django shopping cart",
    license = "MIT License",
    keywords = "django cart bursar",
    url = "http://github.com/hiidef/hiicart"

)
