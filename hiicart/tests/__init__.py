import unittest

import comp, google, core, auditing

__tests__ = [comp, google, core, auditing]

def suite():
    suite = unittest.TestSuite()
    tests = []
    for test in __tests__:
        tl = unittest.TestLoader().loadTestsFromModule(test)
        tests += tl._tests
    suite._tests = tests
    return suite
