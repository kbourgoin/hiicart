from setuptools import setup, find_packages
from hiicart import __version__


# Also requires python-dev and python-openssl
setup(

    name = "HiiCart",

    version = __version__,

    packages = find_packages(),

    install_requires = ['python-dateutil>=1.4', 'simplejson>=2.1.3'],
    include_package_data = True,

    # metadata for upload to PyPI
    author = "Keith Bourgoin",
    author_email = "keith.bourgoin@gmail.com",
    description = "HiiDef django shopping cart",
    license = "MIT License",
    keywords = "django cart bursar",
    url = "http://github.com/hiidef/hiicart"

)
