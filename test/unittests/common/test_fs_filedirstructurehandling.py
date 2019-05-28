
from __future__ import print_function

import os
import sys
import shutil
import tempfile
import filecmp
import logging

import unittest
from unittest.mock import patch, PropertyMock, MagicMock

from muteria.common.fs import FileDirStructureHandling

TMP_DIR_SUFFIX = '.muteria.test.tmp'

class Test_FileDirStructureHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)
        cls._top_dir = os.path.join(cls._worktmpdir, "TD")
        cls._tdkey = "TD_KEY"
        cls._fd_dict = {'a':['a'], 'x_y': ['x','y']}
        with patch.object(sys, 'exit') as sys_exit:
            sys_exit.side_effect = AssertionError
            cls._handler_obj = FileDirStructureHandling(cls._top_dir, \
                                                    cls._tdkey, cls._fd_dict)

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls._worktmpdir):
            shutil.rmtree(cls._worktmpdir)

    def setUp(self):
        os.mkdir(self._top_dir)
        return super().setUp()

    def tearDown(self):
        shutil.rmtree(self._top_dir)
        return super().tearDown()

    #### file

    @patch.object(logging, 'error', return_value=None)
    @patch.object(logging, 'info', return_value=None)
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_resolve(self, sys_exit, l_e, l_i):
        with self.assertRaises(AssertionError):
            self._handler_obj.resolve('x')
        self.assertEqual(self._handler_obj.resolve('a'), 'a')
        self.assertEqual(self._handler_obj.resolve('x_y'), \
                                                        os.path.join('x','y'))

    @patch.object(logging, 'error', return_value=None)
    @patch.object(logging, 'info', return_value=None)
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_get_file_pathname(self, sys_exit, l_e, l_i):
        with self.assertRaises(AssertionError):
            self._handler_obj.get_file_pathname('x')
        self.assertEqual(self._handler_obj.get_file_pathname('a'), \
                                            os.path.join(self._top_dir, 'a'))
        self.assertEqual(self._handler_obj.get_file_pathname('a', True), 'a')

    @patch.object(logging, 'error', return_value=None)
    @patch.object(logging, 'info', return_value=None)
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_get_existing_file_pathname(self, sys_exit, l_e, l_i):
        with self.assertRaises(AssertionError):
            self._handler_obj.get_existing_file_pathname('a')
        with open(self._handler_obj.get_file_pathname('a', rel_path=False), \
                                                                    'w') as f:
            f.write("\n")
        self.assertEqual(\
                self._handler_obj.get_existing_file_pathname('a', True), 'a')

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_file_exists(self, sys_exit):
        self.assertFalse(self._handler_obj.file_exists('a'))
        with open(self._handler_obj.get_file_pathname('a', rel_path=False), \
                                                                    'w') as f:
            f.write("\n")
        self.assertTrue(self._handler_obj.file_exists('a'))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_remove_file_and_get(self, sys_exit):
        fpath = self._handler_obj.get_file_pathname('a', rel_path=False)
        with open(fpath, 'w') as f:
            f.write("\n")
        self.assertEqual(self._handler_obj.remove_file_and_get('a', True), 'a')
        self.assertFalse(os.path.isfile(fpath))

    #### Dir

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_get_dir_pathname(self, sys_exit):
        self.assertEqual(self._handler_obj.get_file_pathname('x_y'), \
                                     self._handler_obj.get_dir_pathname('x_y'))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_dir_exists(self, sys_exit):
        self.assertFalse(self._handler_obj.dir_exists('a'))
        os.mkdir(self._handler_obj.get_file_pathname('a', rel_path=False))
        self.assertTrue(self._handler_obj.dir_exists('a'))

    @patch.object(logging, 'error', return_value=None)
    @patch.object(logging, 'info', return_value=None)
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_get_existing_dir_pathname(self, sys_exit, l_e, l_i):
        with self.assertRaises(AssertionError):
            self._handler_obj.get_existing_dir_pathname('a')
        os.mkdir(self._handler_obj.get_dir_pathname('a', rel_path=False))
        self.assertEqual(\
                self._handler_obj.get_existing_dir_pathname('a', True), 'a')

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_clean_create_and_get(self, sys_exit):
        dpath = self._handler_obj.get_dir_pathname('x_y', rel_path=False)
        self._handler_obj.get_or_create_and_get_dir('x_y')
        tmp_file = os.path.join(dpath, 'tmpp')
        with open(tmp_file, 'w') as f:
            f.write("\n")
        self.assertTrue(os.path.isfile(tmp_file))
        self.assertEqual(\
                    self._handler_obj.clean_create_and_get_dir('x_y', True), \
                    os.path.join('x','y'))
        self.assertFalse(os.path.isfile(tmp_file))
        self.assertTrue(os.path.isdir(dpath))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_get_or_create_and_get_dir(self, sys_exit):
        dpath = self._handler_obj.get_dir_pathname('a', rel_path=False)
        self.assertEqual(\
                self._handler_obj.get_or_create_and_get_dir('a', True), 'a')
        self.assertTrue(os.path.isdir(dpath))

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_remove_dir_and_get(self, sys_exit):
        dpath = self._handler_obj.get_dir_pathname('a', rel_path=False)
        os.mkdir(dpath)
        self.assertEqual(self._handler_obj.remove_dir_and_get('a', True), 'a')
        self.assertFalse(os.path.isdir(dpath))

if __name__ == '__main__':
    verbosity = 2 # TODO: Check why verbosity has no effect here
    testsuite_fdstruct = unittest.TestLoader().loadTestsFromTestCase(\
                                                Test_FileDirStructureHandling)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_fdstruct)

