import logging
import traceback

from django.http import HttpResponse

log = logging.getLogger("hiicart")

def call_func(name, *args, **kwargs):
    """Call a function when all you have is the [str] name and arguments."""
    parts = name.split('.')
    module = __import__(".".join(parts[:-1]), fromlist=[parts[-1]])
    return getattr(module, parts[-1])(*args, **kwargs)

def format_exceptions(method):
    """
    Format exceptions into HttpResponse

    Useful in particular for Google Checkout's integration console.
    The default django error page is displayed as raw html, making
    debugging difficult.
    """
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except:            
            fmt = traceback.format_exc()
            log.error("Exception encountered:")
            log.error(fmt)
            response = HttpResponse(fmt)
            response.status_code=500 # Definitely _not_ a 200 resposne
            return response
    return wrapper
