from __future__ import print_function

import os
import sys
import shutil
import unittest
from unittest.mock import patch
import doctest

import tempfile

import muteria.common.matrices as common_matrices

TMP_DIR_SUFFIX = '.muteria.test.tmp'

class Test_Matrices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)
        cls.filename = os.path.join(cls._worktmpdir, "mat_file.tmp.csv")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._worktmpdir)
    
    def setUp(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)

    def test_serialize(self):
        cols = ['a', 'b', "3@!21"]
        mat = common_matrices.ExecutionMatrix(filename=self.filename,\
                                                        non_key_col_list=cols)
        row1 = {'a':1,'b':0, '3@!21':-1}
        mat.add_row_by_key('k1', row1)
        mat.serialize()
        
        # check
        sep = ' '
        
        self.assertTrue(os.path.isfile(self.filename))

        with open(self.filename) as f:
            line = f.readline()
            self.assertTrue(line)
            line_elems = line.strip().split(sep)
            self.assertEqual(line_elems, [mat.get_key_colname()]+cols)

            line = f.readline()
            self.assertTrue(line)
            line_elems = line.strip().split(sep)
            self.assertEqual(line_elems, ['k1', '1', '0', '-1'])

            line = f.readline()
            self.assertFalse(line)

    def test_create_from_file(self):
        sep = ' '
        with open(self.filename, 'w') as f:
            f.write(sep.join([common_matrices.DEFAULT_KEY_COLUMN_NAME, \
                                                            'a','b','c'])+'\n')
            f.write(sep.join(['x','2','3','1'])+'\n')
        
        mat = common_matrices.ExecutionMatrix(filename=self.filename)
        self.assertEqual(list(mat.get_keys()), ['x'])
        self.assertEqual(list(mat.get_nonkey_colname_list()), ['a','b','c'])
        self.assertEqual(mat.to_pandas_df()['a'][0], 2)
        self.assertEqual(mat.to_pandas_df()['b'][0], 3)
        self.assertEqual(mat.to_pandas_df()['c'][0], 1)

        # TODO: add scenario with loading error (wrong col list...)

def load_tests(loader, tests, ignore):
    """ Doc tests discovery (doctest discovered by unittest)
    """
    tests.addTests(doctest.DocTestSuite(common_matrices))
    return tests

if __name__ == '__main__':
    verbosity = 2

    testsuite_matrices = unittest.TestLoader().loadTestsFromTestCase(\
                                                                Test_Matrices)

    # Doc test suite
    doc_testsuite = unittest.TestSuite()
    doc_testsuite.addTest(doctest.DocTestSuite(common_matrices))

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_matrices)
    unittest.TextTestRunner(verbosity=verbosity).run(doc_testsuite)
