#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""test auditing facilities"""

from unittest import TestCase, main
from hiicart.lib import auditing
from django.views.debug import ExceptionReporter

class AuditingTestCase(TestCase):
    def test_auditing(self):
        def foo():
            return bar()
        def bar():
            return baz()
        def baz():
            return auditing.FakeTraceback()
        tb = foo()
        er = ExceptionReporter(None, type, None, tb)
        # if this fails we've messed up the fake traceback
        html = er.get_traceback_html()


if __name__ == '__main__':
    main()
