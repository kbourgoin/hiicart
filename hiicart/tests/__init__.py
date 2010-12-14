import unittest

import hiicart.tests.comp as comp
import hiicart.tests.google as google
import hiicart.tests.hiicart as hiicart

__tests__ = [comp, google, hiicart]

def suite():
    suite = unittest.TestSuite()
    tests = []
    for test in __tests__:
        tl = unittest.TestLoader().loadTestsFromModule(test)
        tests += tl._tests
    suite._tests = tests
    return suite
