from setuptools import setup, find_packages
# Also requires python-dev and python-openssl
setup(

    name = "HiiCart",

    version = "0.0.2",

    packages = find_packages(),

    install_requires = ['python-dateutil>=1.4', 'simplejson>=2.0.9'],
    include_package_data = True,

    # metadata for upload to PyPI
    author = "Keith Bourgoin",
    author_email = "keith.bourgoin@gmail.com",
    description = "HiiDef django shopping cart",
    license = "MIT License",
    keywords = "django cart bursar",
    url = "http://github.com/kbourgoin/hiicart"

)
