from __future__ import print_function

import sys

import unittest
from unittest.mock import patch

import muteria.common.mix as common_mix

class Test_Confirm_Execution(unittest.TestCase):
    def test_confirm_execution(self):
        yes_stub = lambda _: 'y'
        no_stub = lambda _: 'n'

        if sys.version_info.major < 3:
            import __builtin__
            stored = __builtin__.raw_input
        else:
            import builtins
            stored = builtins.input

        if sys.version_info.major < 3:
            __builtin__.raw_input = yes_stub
        else:
            builtins.input = yes_stub
        self.assertTrue(common_mix.confirm_execution("testing y?"))

        if sys.version_info.major < 3:
            __builtin__.raw_input = no_stub
        else:
            builtins.input = no_stub
        self.assertFalse(common_mix.confirm_execution("testing n?"))

        if sys.version_info.major < 3:
            __builtin__.raw_input = stored
        else:
            builtins.input = stored

class Test_Error_Handler(unittest.TestCase):
    def test_set_repo_mgr(self):
        pass

    def test_error_exit(self):
        pass

    def test_assert_true(self):
        pass

if __name__ == "__main__":
    verbosity = 2
    testsuite_confirm_exec = unittest.TestLoader().loadTestsFromTestCase(\
                                                        Test_Confirm_Execution)
    testsuite_err_handler = unittest.TestLoader().loadTestsFromTestCase(\
                                                        Test_Error_Handler)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_confirm_exec)
    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_err_handler)