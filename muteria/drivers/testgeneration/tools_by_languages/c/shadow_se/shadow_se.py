
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import re

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.drivers.testgeneration.base_testcasetool import BaseTestcaseTool
from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject
from muteria.drivers import DriversUtils

from muteria.drivers.testgeneration.tools_by_languages.c.klee.klee \
                                                    import TestcasesToolKlee

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesToolShadowSE(TestcasesToolKlee):
    """ Make sure to set the path to binarydir in user customs to use this
        The path to binary should be set to the path to the shadow 
        directory. in Shadow VM, it should be '/home/shadowvm/shadow'
    """
    def __init__(self, *args, **kwargs):
        TestcasesToolKlee.__init__(self, *args, **kwargs)
        ERROR_HANDLER.assert_true(self.custom_binary_dir is not None, \
                        "Custom binary dir must be set for shadow", __file__)
        self.shadow_folder_path = os.sep.join(\
                                    os.path.abspath(self.custom_binary_dir)\
                                    .split(os.sep)[:-3])
        self.llvm_29_compiler_path = os.path.join(self.shadow_folder_path, \
                                    "kleeDeploy/llvm-2.9/Release+Asserts/bin")
        self.llvm_gcc_path = os.path.join(self.shadow_folder_path, \
                                'kleeDeploy/llvm-gcc4.2-2.9-x86_64-linux/bin')
        self.wllvm_path = os.path.join(self.shadow_folder_path, \
                                            'kleeDeploy/whole-program-llvm')
    #~ def __init__()

    # SHADOW override
    def _get_default_params(self):
        bool_params = {
            '-ignore-solver-failures': None,
            '-allow-external-sym-calls': True, #None,
            '-posix-runtime': True, #None,
            '-dump-states-on-halt': True, #None,
            #'-only-output-states-covering-new': True 
            '--zest': True,
            '--shadow': True,
            '-emit-all-errors': True,
            '-no-std-out': True,
        }
        key_val_params = {
            #'-output-dir': self.tests_storage_dir,
            #'-solver-backend': None,
            '-search': None,
            '-max-memory': None,
            '-max-time': self.config.TEST_GENERATION_MAXTIME,
            '-libc': 'uclibc',
            '-use-shadow-version': 'product',
            '-program-name': None, #TODO: CHeck importance
            '-shadow-allow-allocs': 'true',
            '-watchdog': 'true',
            '-shadow-replay-standalone': 'false',
        }
        return bool_params, key_val_params
    #~ def _get_default_params()
    
    # SHADOW override
    def _get_sym_args(self):
        # sym args
        default_sym_args = [] #['-sym-arg', '5']
        klee_sym_args = default_sym_args

        #klee_sym_args = default_sym_args
        #uc = self.config.get_tool_user_custom()
        #if uc is not None:
        #    post_bc_cmd = uc.POST_TARGET_CMD_ORDERED_FLAGS_LIST
        #    if post_bc_cmd is not None:
        #        klee_sym_args = []
        #        for tup in post_bc_cmd:
        #            klee_sym_args += list(tup)
        return klee_sym_args
    #~ def _get_sym_args()

    # SHADOW should override
    def _get_back_llvm_compiler(self):
        return "llvm-gcc" #'clang'
    #~ def _get_back_llvm_compiler()

    # SHADOW should override
    def _get_back_llvm_compiler_path(self):
        return self.llvm_29_compiler_path 
    #~ def _get_back_llvm_compiler_path()

    # SHADOW should override
    def _call_generation_run(self, runtool, args):
        # Delete any klee-out-*
        for d in os.listdir(self.tests_working_dir):
            if d.startswith('klee-out-'):
                shutil.rmtree(os.path.join(self.tests_working_dir, d))

        call_shadow_wrapper_file = os.path.join(self.tests_working_dir, \
                                                                "shadow_wrap")
        with open(call_shadow_wrapper_file, 'w') as wf:
            wf.write('#! /bin/bash\n\n')
            wf.write(' '.join(['exec', runtool] + args + ['"${@:1}"']) + '\n')
        os.chmod(call_shadow_wrapper_file, 0o775)

        test_list = list(self.code_builds_factory.repository_manager\
                                                        .get_dev_tests_list())

        # Get list of klee_change, klee_get_true/false locations. TODO

        # Filter only tests that cover those locations, 
        # if there is stmt coverage matrix TODO

        # TODO: Add meta testcase tool in base and also give acess to matrices
        # TODO: with access to devtests base tool alias

        # run test
        for test in test_list:
            # execute the test using meta_testtool. TODO

            # copy the klee out
            test_out = os.path.join(self.tests_storage_dir, test)
            os.mkdir(test_out)
            for d in glob.glob(self.tests_working_dir+"/klee-out-*"):
                shutil.move(d, test_out)
            ERROR_HANDLER.assert_true(len(list(os.listdir(test_out))) > 0, \
                                "Shadow generated no test for tescase: "+test,\
                                                                    __file__)
    #~ def _call_generation_run()

    def _do_generate_tests (self, exe_path_map, outputdir, \
                                        code_builds_factory, max_time=None):
        sys.path.insert(0, self.llvm_gcc_path)
        sys.path.insert(0, self.wllvm_path)

        super(TestcasesToolShadowSE, self)._do_generate_tests(\
                                        exe_path_map, outputdir,
                                        code_builds_factory, max_time=max_time)
        
        sys.path.pop(0)
        sys.path.pop(0)
    #~ def _do_generate_tests ()
#~ class TestcasesToolShadowSE