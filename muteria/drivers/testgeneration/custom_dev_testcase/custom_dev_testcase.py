
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging

import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from muteria.drivers.testgeneration.base_testcasetool import BaseTestcaseTool
from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject

ERROR_HANDLER = common_mix.ErrorHandler

class CustomTestcases(BaseTestcaseTool):
    CUSTOM_TEST_TOOLNAME = "custom_devtests"

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        return True
    #~ def installed()

    def get_testcase_info_object(self):
        tc_info_obj = TestcasesInfoObject()
        dtl = self.code_builds_factory.repository_manager.get_dev_tests_list()
        ERROR_HANDLER.assert_true(dtl is not None, "invalid dev_test_list", \
                                                                    __file__)
        for tc in dtl:
            tc_info_obj.add_test(tc)
        return tc_info_obj
    #~ def get_testcase_info_object()

    def execute_testcase (self, testcase, exe_path_map, env_vars, \
                                            timeout=None, \
                                            use_recorded_timeout_times=None, \
                                            recalculate_execution_times=False, \
                                            with_output_summary=True, \
                                            hash_outlog=True):
        return self._in_repo_execute_testcase(testcase=testcase, \
                                    exe_path_map=exe_path_map, \
                                    env_vars=env_vars, \
                                    timeout=timeout, \
                                    use_recorded_timeout_times=\
                                        use_recorded_timeout_times, \
                                    recalculate_execution_times=\
                                        recalculate_execution_times, \
                                    with_output_summary=with_output_summary, \
                                    hash_outlog=hash_outlog)
    #~ def execute_testcase()

    def runtests(self, testcases, exe_path_map, env_vars, \
                                stop_on_failure=False, per_test_timeout=None, \
                                use_recorded_timeout_times=None, \
                                recalculate_execution_times=False, \
                                with_output_summary=True, hash_outlog=True, \
                                parallel_count=1):
        """ Override runtests
        """
        return self._in_repo_runtests(testcases=testcases, \
                                    exe_path_map=exe_path_map, \
                                    env_vars=env_vars, \
                                    stop_on_failure=stop_on_failure, \
                                    per_test_timeout=per_test_timeout, \
                                    use_recorded_timeout_times=\
                                            use_recorded_timeout_times, \
                                    recalculate_execution_times=\
                                            recalculate_execution_times, \
                                    with_output_summary=with_output_summary, \
                                    hash_outlog=hash_outlog, \
                                    parallel_count=parallel_count)
    #~ def runtests()

    def _prepare_executable(self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Make sure we have the right executable ready (if needed)
        """
        #self.code_builds_factory.copy_into_repository(exe_path_map)
        
        wrapper_obj = self.code_builds_factory.repository_manager.\
                                                        get_wrapper_object()
        if wrapper_obj is not None:
            wrapper_obj.install_wrapper(exe_path_map, collect_output)
    #~ def _prepare_executable()

    def _restore_default_executable(self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Restore back the default executable (if needed).
            Useful for test execution that require the executable
            at a specific location.
        """
        #self.code_builds_factory.restore_repository_files(exe_path_map)
        
        wrapper_obj = self.code_builds_factory.repository_manager.\
                                                        get_wrapper_object()
        if wrapper_obj is not None:
            wrapper_obj.uninstall_wrapper(exe_path_map)
    #~ def _restore_default_executable()

    def _execute_a_test (self, testcase, exe_path_map, env_vars, \
                                callback_object=None, timeout=None, \
                                                    collect_output=None):
        """ Execute a test given that the executables have been set 
            properly
        """
        if timeout is None:
            timeout = self.config.ONE_TEST_EXECUTION_TIMEOUT

        #logging.debug('TIMEOUT: '+str(timeout))

        rep_mgr = self.code_builds_factory.repository_manager

        wrapper_obj = rep_mgr.get_wrapper_object()

        if collect_output:
            # possibly existing wrapper data logs are 
            # removed during wrapper install

            collected_output = []
        else:
            collected_output = None
        
        pre,verdict,post = rep_mgr.run_dev_test(dev_test_name=testcase, \
                                exe_path_map=exe_path_map, \
                                env_vars=env_vars, \
                                timeout=timeout,\
                                collected_output=(collected_output \
                                            if wrapper_obj is None else None),\
                                callback_object=callback_object)
        ERROR_HANDLER.assert_true(\
                            pre == common_mix.GlobalConstants.COMMAND_SUCCESS,\
                                            "before command failed", __file__)
        ERROR_HANDLER.assert_true(\
                        post != common_mix.GlobalConstants.COMMAND_FAILURE,\
                                            "after command failed", __file__)

        # abort is test execution error
        if verdict == common_mix.GlobalConstants.TEST_EXECUTION_ERROR:
            ERROR_HANDLER.error_exit("Test Execution error in "
                                "custom_dev_testcase for test: "+testcase,\
                                                                    __file__)

        # wrapper cleanup
        if wrapper_obj is not None:
            if collect_output:
                wrapper_obj.collect_output(exe_path_map, collected_output, \
                                                                    testcase)
            wrapper_obj.cleanup_logs(exe_path_map)

        return verdict, collected_output
    #~ def _execute_a_test()

    def _do_generate_tests (self, exe_path_map, outputdir, \
                                        code_builds_factory, max_time=None):
        #tc_inf_obj = self.get_testcase_info_object()
        pass
    #~ def _do_generate_tests()
#~ class CustomTestcases
