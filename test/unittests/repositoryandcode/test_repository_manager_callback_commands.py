
from __future__ import print_function

import os
import sys
import time
import shutil
import tempfile
import filecmp
import logging

import unittest
from unittest.mock import patch, PropertyMock, MagicMock

import muteria.repositoryandcode.repository_manager as rm
from muteria.repositoryandcode.callback_object import DefaultCallbackObject

TMP_DIR_SUFFIX = '.muteria.test.tmp'

class Test_RepositoryManager_Command(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)
        cls._repodir = os.path.join(cls._worktmpdir, "repodir")
        cls._src1 = os.path.join(cls._repodir, "src1")
        os.mkdir(cls._repodir)
        with open(cls._src1, 'w') as f:
            f.write("src1")
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            cls.rep_mgr_pass = rm.RepositoryManager(cls._repodir, \
                            dev_test_runner_func=lambda *a, **kw: True, \
                            code_builder_func=lambda *a, **kw: True)
            cls.rep_mgr_fail = rm.RepositoryManager(cls._repodir, \
                            dev_test_runner_func=lambda *a, **kw: False, \
                            code_builder_func=lambda *a, **kw: False)

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls._worktmpdir):
            shutil.rmtree(cls._worktmpdir)

        
    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_run_dev_test(self, li, le,sys_exit):
        res = self.rep_mgr_pass.run_dev_test("anything")
        self.assertEqual(res, (True, True, None))
        res = self.rep_mgr_fail.run_dev_test("anything")
        self.assertEqual(res, (True, False, None))
        res = self.rep_mgr_pass.run_dev_test("anything", \
                                    callback_object=DefaultCallbackObject())
        self.assertEqual(res, (True, True, True))
        res = self.rep_mgr_fail.run_dev_test("anything", \
                                    callback_object=DefaultCallbackObject())
        self.assertEqual(res, (True, False, False))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_build_code(self, li, le,sys_exit):
        res = self.rep_mgr_pass.build_code()
        self.assertEqual(res, (True, True, None))
        res = self.rep_mgr_fail.build_code()
        self.assertEqual(res, (True, False, None))
        res = self.rep_mgr_pass.build_code( \
                                    callback_object=DefaultCallbackObject())
        self.assertEqual(res, (True, True, True))
        res = self.rep_mgr_fail.build_code( \
                                    callback_object=DefaultCallbackObject())
        self.assertEqual(res, (True, False, False))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_custom_read_access(self, li, le,sys_exit):
        res = self.rep_mgr_pass.custom_read_access( \
                                    callback_object=DefaultCallbackObject())
        self.assertEqual(res, (True, True))

if __name__ == "__main__":
    verbosity = 2 # TODO: Check why verbosity has no effect here
    testsuite_rep_mgr = unittest.TestLoader().loadTestsFromTestCase(\
                                            Test_RepositoryManager_Command)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_rep_mgr)