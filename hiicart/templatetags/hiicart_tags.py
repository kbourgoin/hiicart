from django import template
from django.db import models

class HiiCartTemplateError(Exception):
  pass

register = template.Library()

_google_periods = {(1, "DAY"): "DAILY",
                   (7, "DAY"): "WEEKLY",
                   (15, "DAY"): "SEMI_MONTHLY",
                   (1, "MONTH"): "MONTHLY",
                   (2, "MONTH"): "EVERY_TWO_MONTHS",
                   (3, "MONTH"): "QUARTERLY",
                   (365, "YEAR"): "YEARLY",
                   (12, "MONTH"): "YEARLY"}

@register.simple_tag
def google_recur_period(item):
    """Get the Google-friendly subscription period.

    Valid values are DAILY, WEEKLY, SEMI_MONTHLY, MONTHLY, 
    EVERY_TWO_MONTHS, QUARTERLY, and YEARLY.
    """
    period = (item.duration, item.duration_unit)
    if period not in _google_periods:
      raise HiiCartTemplateError("Invalid subscription period provided for Google Checkout.")
    return _google_periods[period]
google_recur_period.is_safe = True
