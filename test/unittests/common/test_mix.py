from __future__ import print_function

import sys

import importlib

import unittest
from unittest.mock import patch, PropertyMock, MagicMock
import doctest

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
    def tearDown(self):
        if sys.version_info.major < 3:
            reload(common_mix)
        else:
            importlib.reload(common_mix)
        

    def test_set_repo_mgr(self):
        if sys.version_info.major < 3:
            reload(common_mix)
        else:
            importlib.reload(common_mix)
        rep_mgr = "MGR" #  just use a string for simplicity
        with patch.object(common_mix.ErrorHandler, 'error_exit') as mf_ee:
            mf_ee.side_effect = AssertionError
            common_mix.ErrorHandler.set_corresponding_repos_manager(rep_mgr)


            self.assertEqual(common_mix.ErrorHandler.repos_dir_manager, \
                                                                    rep_mgr)

            # can only change one (This calls the side effect of mf_ee)
            with self.assertRaises(AssertionError):
                common_mix.ErrorHandler.set_corresponding_repos_manager(None)

    @patch.object(common_mix, 'confirm_execution')
    @patch.object(common_mix.logging, 'error', return_value=None)
    @patch.object(common_mix.logging, 'info', return_value=None)
    def test_error_exit_notconfirm_revert(self, log_inf, log_err, confirm):
        with patch.object(sys, 'exit') as sys_exit:
            sys_exit.side_effect = AssertionError

            confirm.reset_mock()
            confirm.return_value = False
            common_mix.ErrorHandler.repos_dir_manager = PropertyMock()
            common_mix.ErrorHandler.repos_dir_manager.return_value = \
                                                                    MagicMock()
            common_mix.ErrorHandler.repos_dir_manager.revert_repository = \
                                                MagicMock(return_value=None)
            with self.assertRaises(AssertionError):
                common_mix.ErrorHandler.error_exit()
            confirm.assert_called_once()
            common_mix.ErrorHandler.repos_dir_manager.revert_repository.\
                                                        assert_not_called()

    @patch.object(common_mix, 'confirm_execution')
    @patch.object(common_mix.logging, 'error', return_value=None)
    @patch.object(common_mix.logging, 'info', return_value=None)
    def test_error_exit_confirm_revert_ok(self, log_inf, log_err, confirm):
        with patch.object(sys, 'exit') as sys_exit:
            sys_exit.side_effect = AssertionError
            confirm.reset_mock()
            confirm.return_value = True
            common_mix.ErrorHandler.repos_dir_manager = PropertyMock()
            common_mix.ErrorHandler.repos_dir_manager.return_value = \
                                                                    MagicMock()
            common_mix.ErrorHandler.repos_dir_manager.revert_repository = \
                                                MagicMock(return_value=None)
            with self.assertRaises(AssertionError):
                common_mix.ErrorHandler.error_exit()
            confirm.assert_called_once()
            common_mix.ErrorHandler.repos_dir_manager.revert_repository.\
                                                        assert_called_once()


    @patch.object(common_mix, 'confirm_execution')
    @patch.object(common_mix.logging, 'error', return_value=None)
    @patch.object(common_mix.logging, 'info', return_value=None)
    def test_error_exit_confirm_revert_notok(self, log_inf, log_err, confirm):
        with patch.object(sys, 'exit') as sys_exit:
            def rr(*args, **kwargs):
                common_mix.ErrorHandler.error_exit()
            sys_exit.side_effect = AssertionError
            confirm.reset_mock()
            confirm.return_value = True
            common_mix.ErrorHandler.repos_dir_manager = PropertyMock()
            common_mix.ErrorHandler.repos_dir_manager.return_value = \
                                                                    MagicMock()
            common_mix.ErrorHandler.repos_dir_manager.revert_repository = \
                                                MagicMock(return_value=None)
            common_mix.ErrorHandler.repos_dir_manager.revert_repository.\
                            side_effect = rr
            with self.assertRaises(AssertionError):
                common_mix.ErrorHandler.error_exit()
            confirm.assert_called_once()
            common_mix.ErrorHandler.repos_dir_manager.revert_repository.\
                                                        assert_called_once()

    def test_assert_true(self):
        with patch.object(common_mix.ErrorHandler, 'error_exit') as mf_ee:
            mf_ee.side_effect = AssertionError
            common_mix.ErrorHandler.assert_true(True)
            with self.assertRaises(AssertionError):
                common_mix.ErrorHandler.assert_true(False)

def load_tests(loader, tests, ignore):
    """ Doc tests discovery (doctest discovered by unittest)
    """
    tests.addTests(doctest.DocTestSuite(common_mix))
    return tests

if __name__ == "__main__":
    # to run this, do this form the repo root dir:
    # > PYTHONPATH='.' python test/unittests/common/test_mix.py

    verbosity = 2
    testsuite_confirm_exec = unittest.TestLoader().loadTestsFromTestCase(\
                                                        Test_Confirm_Execution)
    testsuite_err_handler = unittest.TestLoader().loadTestsFromTestCase(\
                                                        Test_Error_Handler)

    # Doc test suite
    doc_testsuite = unittest.TestSuite()
    doc_testsuite.addTest(doctest.DocTestSuite(common_mix))
    #doc_testsuite.addTest(doctest.DocFileSuite('doctest_in_help.rst'))

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_confirm_exec)
    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_err_handler)
    unittest.TextTestRunner(verbosity=verbosity).run(doc_testsuite)