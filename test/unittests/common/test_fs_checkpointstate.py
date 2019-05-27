
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

from muteria.common.fs import CheckpointState

TMP_DIR_SUFFIX = '.muteria.test.tmp'

class Test_CheckpointState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)
        cls._cp_file = os.path.join(cls._worktmpdir, "cp_file")
        cls._cp_file_bak = os.path.join(cls._worktmpdir, "cp_file_bak")
        cls._dep_file = os.path.join(cls._worktmpdir, "dep_cp_file")
        cls._dep_file_bak = os.path.join(cls._worktmpdir, "dep_cp_file_bak")

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls._worktmpdir):
            shutil.rmtree(cls._worktmpdir)

    def setUp(self):
        if os.path.isfile(self._cp_file):
            os.remove(self._cp_file)
        if os.path.isfile(self._cp_file_bak):
            os.remove(self._cp_file_bak)
        if os.path.isfile(self._dep_file):
            os.remove(self._dep_file)
        if os.path.isfile(self._dep_file_bak):
            os.remove(self._dep_file_bak)
        with patch.object(sys, 'exit') as sys_exit:
            sys_exit.side_effect = AssertionError
            self._cp_obj = CheckpointState(self._cp_file, self._cp_file_bak)
        return super().setUp()

    def tearDown(self):
        with patch.object(sys, 'exit') as sys_exit:
            sys_exit.side_effect = AssertionError
            self._cp_obj.destroy_checkpoint()
        return super().tearDown()

    def test_add_dep_checkpoint_state(self):
        dep = CheckpointState(self._dep_file, self._dep_file_bak)
        self._cp_obj.add_dep_checkpoint_state(dep)
        self.assertIn(dep, self._cp_obj.get_dep_checkpoint_states()) 

    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_destroy_checkpoint(self, sys_exit):
        self._cp_obj.restart_task()
        self.assertFalse(self._cp_obj.is_destroyed())
        self._cp_obj.destroy_checkpoint()
        self.assertTrue(self._cp_obj.is_destroyed())

        with patch.object(CheckpointState, 'destroy_checkpoint', \
                                            return_value=None) as mock_destroy:
            dep = CheckpointState(self._dep_file, self._dep_file_bak)
            dep.destroy_checkpoint = MagicMock(return_value=None)
            self._cp_obj.add_dep_checkpoint_state(dep)
            self._cp_obj.destroy_checkpoint()
        mock_destroy.assert_called_once()

    # TODO: Maybe make nicer test
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test__(self, sys_exit):
        
        with self.assertRaises(AssertionError):
            self._cp_obj.get_execution_time()
            self._cp_obj.get_detailed_execution_time()

        self.assertTrue(self._cp_obj.is_destroyed())
        self.assertFalse(self._cp_obj.is_finished())

        self._cp_obj.restart_task()
        self.assertLessEqual(0.0, self._cp_obj.get_execution_time())
        self.assertFalse(self._cp_obj.is_finished())
        self.assertFalse(self._cp_obj.is_destroyed())
        self._cp_obj.destroy_checkpoint()
        self.assertTrue(self._cp_obj.is_destroyed)
        
        s_time = time.time()
        r = self._cp_obj.load_checkpoint_or_start()
        self.assertIsNone(r)
        self._cp_obj.write_checkpoint([1,2,3], detailed_exectime_obj={'x':3})
        tmp = CheckpointState(self._cp_file, self._cp_file_bak)
        r, dt = tmp.load_checkpoint_or_start(ret_detailed_exectime_obj=True)
        self.assertEqual(r, [1,2,3])
        self.assertEqual(dt, {'x':3})
        tmp.set_finished()
        self.assertTrue(tmp.is_finished)
        self.assertLessEqual(tmp.get_execution_time(), time.time() - s_time) 

if __name__ == "__main__":
    verbosity = 2 # TODO: Check why verbosity has no effect here
    testsuite_cps = unittest.TestLoader().loadTestsFromTestCase(\
                                                    Test_CheckpointState)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_cps)