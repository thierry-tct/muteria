from __future__ import print_function
import os, sys
import shutil
import tempfile
import filecmp
import json
import pandas as pd

import unittest
import doctest

import muteria.common.fs as common_fs

TMP_DIR_SUFFIX = '.muteria.test.tmp'

class Test_JSON_CSV(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._worktmpdir)

    def test_loadJSON(self):
        jfilename = os.path.join(self._worktmpdir, "jsontmp.json")
        exp = {"x":1, "y":[2,3,"zz"]}
        with open(jfilename, 'w') as fp:
            fp.write(str(exp).replace("'", '"'))
        res = common_fs.loadJSON(jfilename)
        # load Json worked fine
        self.assertEqual(res, exp)
        os.remove(jfilename)

    def test_dumpJSON(self):
        jfilename = os.path.join(self._worktmpdir, "jsontmp.json")
        exp = {"x":1, "y":[2,3,"zz"]}
        res = common_fs.dumpJSON(exp, jfilename)
        # dumpJSON succeded
        self.assertEqual(res, None)
        
        with open(jfilename) as fp:
            res = json.load(fp)
        # dumpJSON was correct
        self.assertEqual(res, exp)
        os.remove(jfilename)

    def test_loadCSV(self):
        cfilename = os.path.join(self._worktmpdir, "csvtmp.csv")
        exp = pd.DataFrame({'x':[1,3], 'y':[2,4]})

        # default separator: space
        with open (cfilename, "w") as fp:
            fp.write("x y\n1 2\n3 4\n")
        resdf = common_fs.loadCSV(cfilename)
        self.assertTrue(resdf.equals(exp))

        # another separator: ','
        with open (cfilename, "w") as fp:
            fp.write("x,y\n1,2\n3,4\n")
        resdf = common_fs.loadCSV(cfilename, separator=',')
        self.assertTrue(resdf.equals(exp))

        os.remove(cfilename)

    def test_dumpCSV(self):
        cfilename = os.path.join(self._worktmpdir, "csvtmp.csv")
        df = pd.DataFrame({'x':[1,3], 'y':[2,4]})
        
        # default separator: space
        res = common_fs.dumpCSV(df, cfilename)
        # dumpJSON succeded
        self.assertEqual(res, None)
        with open(cfilename) as fp:
            res = fp.read()
        exp = "x y\n1 2\n3 4\n"
        # Data is okay
        self.assertEqual(res, exp)
        os.remove(cfilename)

        # another separator: ','
        res = common_fs.dumpCSV(df, cfilename, separator=',')
        # dumpJSON succeded
        self.assertEqual(res, None)
        with open(cfilename) as fp:
            res = fp.read()
        exp = "x,y\n1,2\n3,4\n"
        # Data is okay
        self.assertEqual(res, exp)
        os.remove(cfilename)

class Test_Compress_Decompress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._worktmpdir = tempfile.mkdtemp(suffix=TMP_DIR_SUFFIX)
        cls.targetd = os.path.join(cls._worktmpdir, 'tartmpdir')
        os.mkdir(cls.targetd)
        # make targetd have the following files: 
        # first1, first2, secondd/deepfile
        with open(os.path.join(cls.targetd, "first1"), 'w') as fp:
            fp.write("first1\n")
        with open(os.path.join(cls.targetd, "first2"), 'w') as fp:
            fp.write("first2\n")
        os.mkdir(os.path.join(cls.targetd, "secondd"))
        with open(os.path.join(cls.targetd, "secondd", "deepfile"), 'w') as fp:
            fp.write("deepfile\n")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._worktmpdir)

    def test_targz_compress_decompress(self):
        copy_targetd = os.path.join(self._worktmpdir, "copytartmpdir")
        other_copy_targetd = copy_targetd+"-other"
        tar_copy_targetd = copy_targetd+".tar.gz"
        other_tar_copy_targetd = other_copy_targetd+".tar.gz"

        # Clean
        for d in [copy_targetd, other_copy_targetd]:
            if os.path.isdir(d):
                shutil.rmtree(d)
        for f in [tar_copy_targetd, other_tar_copy_targetd]:
            if os.path.isfile(f):
                os.remove(f)

        shutil.copytree(self.targetd, copy_targetd)

        # compress without remove source and no specified out
        ## Check that in is not changed
        # then compress withe remove source and specified out
        ## Check that in is removed and both previous out and this are same
        # Repreat above steps with decompress

        # Compress Default
        res = common_fs.TarGz.compressDir(copy_targetd)
        self.assertEqual(res, None)

        # make sure the out file is generated
        self.assertTrue(os.path.isfile(tar_copy_targetd))
        # make sure that nothing was changed on the input dir
        dcmp = filecmp.dircmp(self.targetd, copy_targetd)
        self.assertEqual(len(dcmp.left_only), 0)
        self.assertEqual(len(dcmp.right_only), 0)

        # Compress Params
        res = common_fs.TarGz.compressDir(copy_targetd, 
                                    out_archive_pathname=other_tar_copy_targetd,
                                    remove_in_directory=True)
        self.assertEqual(res, None)
        # Make sure that in dir was removed and the tar files are same
        self.assertFalse(os.path.isdir(copy_targetd))
        #self.assertEqual(filecmp.cmp(other_tar_copy_targetd, tar_copy_targetd))

        ###

        # Decompress Default
        res = common_fs.TarGz.decompressDir(tar_copy_targetd)
        self.assertEqual(res, None)

        # make sure decompress keeps tar file by default
        self.assertTrue(os.path.isfile(tar_copy_targetd))
        self.assertTrue(os.path.isdir(copy_targetd))

        # make sure that both compression and decompression worked
        dcmp = filecmp.dircmp(self.targetd, copy_targetd)
        self.assertEqual(len(dcmp.left_only), 0)
        self.assertEqual(len(dcmp.right_only), 0)

        # Decompress Params
        res = common_fs.TarGz.decompressDir(tar_copy_targetd,
                                    out_directory=other_copy_targetd,
                                    remove_in_archive=True)
        self.assertEqual(res, None)

        # make sure decompress removes tar file by default
        self.assertFalse(os.path.isfile(tar_copy_targetd))

        # make sure that both compression and decompression worked
        dcmp = filecmp.dircmp(self.targetd, other_copy_targetd)
        self.assertEqual(len(dcmp.left_only), 0)
        self.assertEqual(len(dcmp.right_only), 0)

        ###

        # Clean
        for d in [copy_targetd, other_copy_targetd]:
            if os.path.isdir(d):
                shutil.rmtree(d)
        for f in [tar_copy_targetd, other_tar_copy_targetd]:
            if os.path.isfile(f):
                os.remove(f)
        
def load_tests(loader, tests, ignore):
    """ Doc tests discovery (doctest discovered by unittest)
    """
    tests.addTests(doctest.DocTestSuite(common_fs))
    return tests

if __name__ == "__main__":
    #unittest.main()
    verbosity = 2 # TODO: Check why verbosity has no effect here
    testsuite_json_csv = \
                    unittest.TestLoader().loadTestsFromTestCase(Test_JSON_CSV)
    testsuite_compress_decompress = \
                                unittest.TestLoader().loadTestsFromTestCase(\
                                                    Test_Compress_Decompress)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_json_csv)
    unittest.TextTestRunner(verbosity=verbosity).run(\
                                                testsuite_compress_decompress)

