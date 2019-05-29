

from __future__ import print_function

import os
import sys
import logging

import unittest
from unittest.mock import patch, PropertyMock, MagicMock

from muteria.repositoryandcode.codes_convert_support \
                                    import IdentityCodeConverter, CodeFormats
from muteria.repositoryandcode.repository_manager import RepositoryManager
from muteria.repositoryandcode.code_builds_factory import CodeBuildsFactory
import muteria.repositoryandcode.codes_convert_support as ccs

class Test_CodeBuildsFactory(unittest.TestCase):
    @patch.object(logging, 'error', return_value=None)
    @patch.object(logging, 'info', return_value=None)
    @patch.object(sys, 'exit', side_effect=AssertionError)
    def test_all(self, sys_exit, l_e, l_i):
        rep_mgr = None
        cb = CodeBuildsFactory(repository_manager=rep_mgr)
        i_cc1 = ccs.IdentityCodeConverter()
        i_cc2 = ccs.IdentityCodeConverter()
        i_cc1.convert_code = MagicMock(return_value='i_cc1')
        i_cc2.convert_code = MagicMock(return_value='i_cc2')
        src_fmt = CodeFormats.C_SOURCE
        dest_fmt = CodeFormats.CPP_SOURCE
        cb.override_registration(src_fmt, dest_fmt, i_cc2)
        cb.override_registration(src_fmt, dest_fmt, i_cc1)
        ret = cb.transform_src_into_dest(src_fmt, dest_fmt, {})
        self.assertEqual(ret, 'i_cc1')
        i_cc1.convert_code.assert_called_once_with(src_fmt, dest_fmt, {}, \
                                                    repository_manager=rep_mgr)

        with self.assertRaises(AssertionError):
            cb.transform_src_into_dest("invalid_src@@@", "invalid_dest@@@", {})
            cb.transform_src_into_dest(src_fmt, "invalid_dest@@@", {})

if __name__ == '__main__':
    verbosity = 2 # TODO: Check why verbosity has no effect here
    testsuite = unittest.TestLoader().loadTestsFromTestCase(\
                                                        Test_CodeBuildsFactory)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite)

