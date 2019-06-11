
import unittest
import doctest

import lib.lib as l

class Test_Lib(unittest.TestCase):
    def test_get_even_(self):
        lobj = l.Lib()
        r=lobj.get_even_total(1, 2)
        self.assertEqual(r, 2)

    def test_get_odd_(self):
        lobj = l.Lib()
        r=lobj.get_odd_total(1, 2)
        self.assertEqual(r, 1)


def load_tests(loader, tests, ignore):
    """ Doc tests discovery (doctest discovered by unittest)
    """
    tests.addTests(doctest.DocTestSuite(l))
    return tests

if __name__ == '__name__':
    ts = unittest.TestLoader().loadTestsFromTestCase(Test_Lib)

    doc_ts = unittest.TestSuite()
    doc_ts.addTest(doctest.DocTestSuite(l))

    unittest.TextTestRunner(verbosity=2).run(ts)
    unittest.TextTestRunner(verbosity=2).run(doc_ts)