#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""auditing for hiicart, relies on sentry (probably)"""

import inspect
import logging
from django.views.debug import ExceptionReporter

try:
    from sentry.client.models import get_client
except ImportError:
    print "You must be using django-sentry to use hiicart auditing."
    get_client = lambda: None

class AuditingStacktrace(Exception):
    def __init__(self, *args, **kwargs):
        if not args:
            args[0] = "(Auditing Stacktrace)"
        super(AuditingStacktrace, self).__init__(*args, **kwargs)

class FakeTraceback(object):
    """A fake traceback object that lets us log a stack trace whenever we want,
    not just when an exception occurs and we get a traceback."""
    def __init__(self, stack=None):
        self._stack = stack or inspect.stack()[1:]
        self._frames = [s[0] for s in self._stack]
        self.tb_frame = self._frames[0]
        self.tb_lineno = self._stack[0][2]

    def get_next(self):
        if len(self._stack) == 1:
            return None
        return FakeTraceback(self._stack[1:])
    tb_next = property(get_next)

    def get_traceback_html(self, request):
        er = ExceptionReporter(request, AuditingStacktrace, AuditingStacktrace(), self)
        return er.get_traceback_html()

def log_with_stacktrace(message):
    client = get_client()
    if client is None:
        logger = logging.get_logger()
        logger.warn("Could not save stack trace for message: %s" % message)
        return
    stack = inspect.stack()[1:]
    tb = FakeTraceback(stack)
    exc_info = (AuditingStacktrace, AuditingStacktrace(message), tb)
    get_client().create_from_exception(exc_info)

