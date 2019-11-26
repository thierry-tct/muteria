
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import resource

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.drivers.testgeneration.base_testcasetool import BaseTestcaseTool
from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject
from muteria.drivers import DriversUtils
from muteria.drivers.testgeneration.testcase_formats.ktest.ktest \
                                                        import KTestTestFormat
from muteria.drivers.testgeneration.tools_by_languages.c.klee.klee \
                                                    import TestcasesToolKlee

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesToolSemu(TestcasesToolKlee):

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        for prog in ('klee-semu',):
            if custom_binary_dir is not None:
                prog = os.path.join(custom_binary_dir, prog)
            if not DriversUtils.check_tool(prog=prog, args_list=['--version'],\
                                                    expected_exit_codes=[0,1]):
                return False

        return KTestTestFormat.installed(custom_binary_dir=custom_binary_dir)
    #~ def installed()

    def __init__(self, *args, **kwargs):
        BaseTestcaseTool.__init__(self, *args, **kwargs)
        self.test_details_file = \
                    os.path.join(self.tests_working_dir, 'test_details.json')
        self.klee_used_tmp_build_dir = os.path.join(self.tests_working_dir, \
                                                    'klee_used_tmp_build_dir')

        # mapping between exes, to have a local copy for execution
        self.repo_exe_to_local_to_remote = {}

        if os.path.isdir(self.klee_used_tmp_build_dir):
            shutil.rmtree(self.klee_used_tmp_build_dir)
        os.mkdir(self.klee_used_tmp_build_dir)
    #~ def __init__()

    # SHADOW override
    def _get_default_params(self):
        bool_params = {
            '-ignore-solver-failures': None,
            '-allow-external-sym-calls': True, #None,
            '-posix-runtime': True, #None,
            '-dump-states-on-halt': True, #None,
            '-only-output-states-covering-new': True 
        }
        key_val_params = {
            '-output-dir': self.tests_storage_dir,
            '-solver-backend': None,
            '-search': None,
            '-max-memory': None,
            '-max-time': self.config.TEST_GENERATION_MAXTIME,
            '-libc': 'uclibc',
        }
        return bool_params, key_val_params
    #~ def _get_default_params()
    
    def _get_tool_name(self):
        return 'klee-semu'
    #~ def _get_tool_name()
    
#~ class TestcasesToolSemu