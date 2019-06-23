
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.drivers.testgeneration.base_testcasetool import BaseTestcaseTool
from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject
from muteria.drivers import DriversUtils

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesToolKlee(BaseTestcaseTool):

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        for prog in ('klee', 'klee-replay'):
            if not DriversUtils.check_tool(prog=prog, args_list=['--version'],\
                                                    expected_exit_codes=[0]):
                return False
        return True
    #~ def installed()

    def __init__(self, *args, **kwargs):
        BaseTestcaseTool.__init__(self, *args, **kwargs)
        self.test_details_file = \
                    os.path.join(self.tests_working_dir, 'test_details.json')
    #~ def __init__()

    def _get_default_params(self):
        bool_params = {
            '-ignore-solver-failures': None,
            '-allow-external-sym-calls': True, #None,
            '-posix-runtime': True, #None,
            '-dump-states-on-halt': True, #None, 
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

    def get_testcase_info_object(self):
        try:
            return self.testcase_info_object
        except AttributeError:
            tc_info_obj = TestcasesInfoObject()
            for tc in os.listdir(self.tests_storage_dir):
                if tc.endswith('.ktest'):
                    tc_info_obj.add_test(tc)
            self.testcase_info_object = tc_info_obj
            return self.testcase_info_object
    #~ def get_testcase_info_object()

    def _prepare_executable(self, exe_path_map, env_vars):
        """ Make sure we have the right executable ready (if needed)
        """
        #self.code_builds_factory.copy_into_repository(exe_path_map)
        pass
    #~ def _prepare_executable()

    def _restore_default_executable(self, exe_path_map, env_vars):
        """ Restore back the default executable (if needed).
            Useful for test execution that require the executable
            at a specific location.
        """
        #self.code_builds_factory.restore_repository_files(exe_path_map)
        pass
    #~ def _restore_default_executable()

    def _execute_a_test (self, testcase, exe_path_map, env_vars, \
                                        callback_object=None, timeout=None):
        """ Execute a test given that the executables have been set 
            properly
        """
        prog = 'klee-replay'

        if timeout is None:
            timeout = self.config.ONE_TEST_EXECUTION_TIMEOUT
        
        ERROR_HANDLER.assert_true(len(exe_path_map) == 1, \
                                    "support a single exe for now", __file__)
        ERROR_HANDLER.assert_true(callback_object is None, \
                                        'TODO: handle callback_obj', __file__)
        exe = exe_path_map[list(exe_path_map.keys())[0]]
        if exe is None:
            # TODO: CRITICAL: Go though the repo manager or copy elsewhere
            # before using repo exe (paralelism)
            exe = list(exe_path_map.keys())[0]
        args = [exe, os.path.join(self.tests_storage_dir, testcase)]
        tmp_env = os.environ.copy()
        tmp_env['KLEE_REPLAY_TIMEOUT'] = str(timeout)
        retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                    prog=prog, args_list=args, env=tmp_env, \
                                                        merge_err_to_out=True)
        # TODO: Oracle here
        if retcode in (DriversUtils.EXEC_TIMED_OUT_RET_CODE, \
                                    DriversUtils.EXEC_SEGFAULT_OUT_RET_CODE):
            retcode = common_mix.GlobalConstants.FAIL_TEST_VERDICT
        else:
            retcode = common_mix.GlobalConstants.PASS_TEST_VERDICT
        return retcode
    #~ def _execute_a_test()

    def _do_generate_tests (self, exe_path_map, outputdir, \
                                        code_builds_factory, max_time=None):
        # Setup
        if os.path.isdir(self.tests_working_dir):
            shutil.rmtree(self.tests_working_dir)
        os.mkdir(self.tests_working_dir)
        if os.path.isdir(self.tests_storage_dir):
            shutil.rmtree(self.tests_storage_dir)
        
        prog = 'klee'
        default_sym_args = ['-sym-arg', '5']
        back_llvm_compiler = None #'clang'
        
        rel_path_map = {}
        exes, _ = code_builds_factory.repository_manager.\
                                                    get_relative_exe_path_map()
        for exe in exes:
            filename = os.path.basename(exe)
            rel_path_map[exe] = os.path.join(self.tests_working_dir, filename)
        pre_ret, ret, post_ret = code_builds_factory.transform_src_into_dest(\
                        src_fmt=CodeFormats.C_SOURCE,\
                        dest_fmt=CodeFormats.LLVM_BITCODE,\
                        src_dest_files_paths_map=rel_path_map,\
                        compiler=back_llvm_compiler, \
                        clean_tmp=True, reconfigure=True)
        if ret == common_mix.GlobalConstants.TEST_EXECUTION_ERROR:
            ERROR_HANDLER.error_exit("Program {}.".format(\
                                'LLVM built problematic'), __file__)

        # Update exe_map to reflect bitcode extension
        rel2bitcode = {}
        for r_file, b_file in list(rel_path_map.items()):
            bc = b_file+'.bc'
            ERROR_HANDLER.assert_true(os.path.isfile(bc), \
                                    "Bitcode file not existing: "+bc, __file__)
            rel2bitcode[r_file] = bc

        ERROR_HANDLER.assert_true(len(rel_path_map) == 1, \
                            "Support single bitcode module for now", __file__)

        bitcode_file = rel2bitcode[list(rel2bitcode.keys())[0]]
        
        # klee params
        bool_param, k_v_params = self._get_default_params()
        if max_time is not None:
            k_v_params['-max-time'] = str(max_time)

        args = [bp for bp, en in list(bool_param.items()) if en]
        for k,v in list(k_v_params.items()):
            if v is not None:
                args += [k,str(v)]
        args.append(bitcode_file)

        # sym args
        klee_sym_args = default_sym_args
        uc = self.config.get_tool_user_custom()
        if uc is not None:
            post_bc_cmd = uc.POST_TARGET_CMD_ORDERED_FLAGS_LIST
            if post_bc_cmd is not None:
                klee_sym_args = []
                for tup in post_bc_cmd:
                    klee_sym_args += list(tup)
        args += klee_sym_args

        # Execute Klee
        ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                                                    prog, args)

        if (ret != 0):
            logging.error(out)
            logging.error(err)
            logging.error("\n>> CMD: " + " ".join([prog]+args))
            ERROR_HANDLER.error_exit("\nmart failed'", __file__)

        store_obj = {r: os.path.basename(b) for r,b in rel2bitcode.items()}
        common_fs.dumpJSON(store_obj, self.test_details_file)
    #~ def _do_generate_tests()
#~ class CustomTestcases