
from __future__ import print_function

import os
import sys
import shutil
import tempfile
import filecmp
import logging

import unittest
from unittest.mock import patch, PropertyMock, MagicMock

from muteria.repositoryandcode.codes_convert_support \
                                    import IdentityCodeConverter, CodeFormats
from muteria.repositoryandcode.repository_manager import RepositoryManager

TMP_DIR_SUFFIX = '.muteria.test.tmp'

from git import Repo as git_repo
import git.exc as git_exc

class Test_IdentityCodeConverter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)
        cls._cachedir = os.path.join(cls._worktmpdir, 'cache')

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls._worktmpdir):
            shutil.rmtree(cls._worktmpdir)

    def setUp(self):
        os.mkdir(self._cachedir)
        return super().setUp()

    def tearDown(self):
        shutil.rmtree(self._cachedir)
        return super().tearDown()

    #### file

    @patch.object(logging, 'error', return_value=None)
    @patch.object(logging, 'info', return_value=None)
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_get_source_formats__get_destination_formats_for(\
                                                    self, sys_exit, l_e, l_i):
        ic = IdentityCodeConverter()
        with self.assertRaises(AssertionError):
            ic.get_source_formats()
            ic.get_destination_formats_for(CodeFormats.C_SOURCE)

    @patch.object(logging, 'error', return_value=None)
    @patch.object(logging, 'info', return_value=None)
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_convert_code(self, sys_exit, l_e, l_i):
        ic = IdentityCodeConverter()

        src_fmt = CodeFormats.JAVASCRIPT_SOURCE
        dest_fmt = CodeFormats.JAVASCRIPT_SOURCE
        fsdmap = {os.path.join(self._cachedir, f): \
                                            os.path.join(self._cachedir, t) \
                                        for f,t in [('a','b'), ('x','y')]}
        for f in fsdmap:
            with open(f, 'w') as fp:
                fp.write('\n')
        
        repo = git_repo.init(self._cachedir)
        rep_mgr = RepositoryManager(self._cachedir)
        ic.convert_code(src_fmt, dest_fmt, fsdmap, rep_mgr)
        for f in fsdmap:
            self.assertTrue(os.path.isfile(fsdmap[f]))

        ###
        with self.assertRaises(AssertionError):
            ic.convert_code(CodeFormats.C_SOURCE, CodeFormats.CPP_SOURCE,\
                                                            fsdmap, rep_mgr)

if __name__ == '__main__':
    verbosity = 2 # TODO: Check why verbosity has no effect here
    testsuite = unittest.TestLoader().loadTestsFromTestCase(\
                                                    Test_IdentityCodeConverter)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite)

