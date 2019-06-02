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

TMP_DIR_SUFFIX = '.muteria.test.tmp'

class Test_RepositoryManager_SetupRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)
        cls._repodir = os.path.join(cls._worktmpdir, "repodir")
        cls._src1 = os.path.join(cls._repodir, "src1")
        cls._src2 = os.path.join(cls._repodir, "src2")
        cls._src3 = os.path.join(cls._repodir, "src3")

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls._worktmpdir):
            shutil.rmtree(cls._worktmpdir)

    def setUp(self):
        os.mkdir(self._repodir)
        for d, s in [('src1', self._src1), ('src2', self._src2), \
                                                        ('src3', self._src3)]:
            self.write_file(s, d)
        return super().setUp()

    def tearDown(self):
        shutil.rmtree(self._repodir)
        return super().tearDown()

    @staticmethod
    def write_file(file_path, data):
        with open(file_path, 'w') as f:
            f.write(data)

    @staticmethod
    def file_contains(file_path, data):
        with open(file_path) as f:
            return f.read() == data

    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_init(self, li, le,sys_exit):
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir)
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[False, False]):
            rep_mgr = rm.RepositoryManager(self._repodir)
        self.tearDown()
        self.setUp()

        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[False, True]):
            with self.assertRaises(AssertionError):
                rep_mgr = rm.RepositoryManager(self._repodir)
            self.tearDown()
            self.setUp()

        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, False]):
            with self.assertRaises(AssertionError):
                rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src1': None})
        
    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_init_srclistoverride(self, li, le,sys_exit):
        # check src list override
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                        source_files_to_objects={'src1': None, 'src2': None})
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src1': None})
            self.write_file(self._src2, "xxx")
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src1': None})
            self.assertTrue(self.file_contains(self._src2, 'xxx'))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_init_noprevuntrack(self, li, le,sys_exit):
        # Different src but no prev untracked
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                        source_files_to_objects={'src1': None, 'src2': None})
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src1': None})
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[False, False]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src2': None})

    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_init_prevuntrack_bypass(self, li, le,sys_exit):
        # Different src with prev untracked and bypass
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src1': None})
        self.write_file(self._src1, "xxx")
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src2': None})
            self.assertTrue(self.file_contains(self._src1, 'xxx'))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_init_prevuntrack_nobypass_revert(self, li, le,sys_exit):
        # Different src with prev untracked and no bypass and revert
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                        source_files_to_objects={'src1': None, 'src2': None})
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src1': None})
        self.write_file(self._src1, "xxx")
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[False, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src2': None})

    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_init_prevuntrack_nobypass_norevert(self, li, le,sys_exit):
        # Different src with prev untracked and no bypass and no revert
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                        source_files_to_objects={'src1': None, 'src2': None})
            rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src1': None})
        self.write_file(self._src1, "xxx")
        #input(self._repodir)
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                side_effect=[False, False]):
            with self.assertRaises(AssertionError):
                rep_mgr = rm.RepositoryManager(self._repodir, \
                                        source_files_to_objects={'src2': None})

    # revert
    @patch.object(sys, 'exit', side_effect=AssertionError)
    @patch.object(rm.common_mix.logging, 'error', return_value=None)
    @patch.object(rm.common_mix.logging, 'info', return_value=None)
    def test_revert_repo(self, li, le,sys_exit):
        # Different src with prev untracked and no bypass and no revert
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                        source_files_to_objects={'src1': None, 'src2': None})
        with self.assertRaises(AssertionError):
            rep_mgr.revert_repository(as_initial=True)
        self.tearDown()
        self.setUp()
        
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                        source_files_to_objects={'src1': None, 'src2': None})
        self.write_file(self._src1, "xxx")
        self.assertTrue(self.file_contains(self._src1, 'xxx'))
        rep_mgr.revert_repository()
        self.assertTrue(self.file_contains(self._src1, 'src1'))
        self.tearDown()
        self.setUp()
        
        with patch.object(rm.common_mix, 'confirm_execution', \
                                                    side_effect=[True, True]):
            rep_mgr = rm.RepositoryManager(self._repodir, \
                        source_files_to_objects={'src1': None, 'src2': None})
        self.write_file(self._src1, "xxx")
        self.assertTrue(self.file_contains(self._src1, 'xxx'))
        rep_mgr.revert_src_list_files()
        self.assertTrue(self.file_contains(self._src1, 'src1'))

# TODO: test for using branch (to revert as_initial)

if __name__ == "__main__":
    verbosity = 2 # TODO: Check why verbosity has no effect here
    testsuite_rep_mgr = unittest.TestLoader().loadTestsFromTestCase(\
                                            Test_RepositoryManager_SetupRepo)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_rep_mgr)