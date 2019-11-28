
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging

import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

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

    def __init__(self, *args, **kwargs):
        BaseTestcaseTool.__init__(self, *args, **kwargs)
        self.test_list_storage_file = os.path.join(self.tests_storage_dir, \
                                                            'test_list.json')
        self.wrapper_obj = self.code_builds_factory.repository_manager.\
                                                        get_wrapper_object()
        self.splittest_ext = '.splittest@'
        self.wrapper_test_splitting = (self.wrapper_obj is not None \
                and self.wrapper_obj.get_test_splitting_wrapper() is not None\
                and not self.config.TESTS_ORACLE_TESTS)
    #~ def __init__()

    def get_testcase_info_object(self):
        tc_info_obj = TestcasesInfoObject()
        ERROR_HANDLER.assert_true(os.path.isfile(self.test_list_storage_file),\
                    "No test list file found, did generation occur?", __file__)
        dtl = common_fs.loadJSON(self.test_list_storage_file)
        for tc, targs in dtl:
            tc_info_obj.add_test(tc)
        return tc_info_obj
    #~ def get_testcase_info_object()

    def execute_testcase (self, testcase, exe_path_map, env_vars, \
                                            timeout=None, \
                                            use_recorded_timeout_times=None, \
                                            recalculate_execution_times=False,\
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
                                hash_outlog=hash_outlog, \
                                copy_exe_to_repo=(self.wrapper_obj is None))
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
                                parallel_count=parallel_count, \
                                copy_exe_to_repo=(self.wrapper_obj is None))
    #~ def runtests()

    def _prepare_executable(self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Make sure we have the right executable ready (if needed)
        """
        #self.code_builds_factory.copy_into_repository(exe_path_map)
        
        if self.wrapper_obj is not None:
            self.wrapper_obj.install_wrapper(exe_path_map, collect_output)
        '''else:
            if exe_path_map is not None:
                repo_root_dir = self.code_builds_factory.repository_manager\
                                                    .get_repository_dir_path()
                for rep_rel_name, abs_name in exe_path_map.items():
                    rep_abs_name = os.path.join(repo_root_dir, rep_rel_name)
                    if abs_name is not None and rep_abs_name != abs_name:
                        # copy to repo
                        try:
                            shutil.copy2(abs_name, rep_abs_name)
                        except PermissionError:
                            os.remove(rep_abs_name)
                            shutil.copy2(abs_name, rep_abs_name)'''
    #~ def _prepare_executable()

    def _restore_default_executable(self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Restore back the default executable (if needed).
            Useful for test execution that require the executable
            at a specific location.
        """
        #self.code_builds_factory.restore_repository_files(exe_path_map)
        
        if self.wrapper_obj is not None:
            self.wrapper_obj.uninstall_wrapper(exe_path_map)
        else:
            self.code_builds_factory.set_repo_to_build_default()
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

        if collect_output:
            # possibly existing wrapper data logs are 
            # removed during wrapper install

            collected_output = []
        else:
            collected_output = None
        
        # change test executor to consider the test ID after @
        runner_testcase = testcase
        if self.wrapper_test_splitting:
            tmp = testcase.split(self.splittest_ext)
            if len(tmp) > 1:
                runner_testcase = ''.join(tmp[:-1])
                subtest_id = tmp[-1]
                st_env_vars = self.wrapper_obj.get_test_splitting_wrapper()\
                                        .get_sub_test_id_env_vars(subtest_id)
                if env_vars is None:
                    env_vars = {}
                env_vars.update(st_env_vars)

        pre,verdict,post = rep_mgr.run_dev_test(dev_test_name=runner_testcase,\
                                exe_path_map=exe_path_map, \
                                env_vars=env_vars, \
                                timeout=timeout,\
                                collected_output=(collected_output \
                                    if self.wrapper_obj is None else None),\
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
        if self.wrapper_obj is not None:
            if collect_output:
                self.wrapper_obj.collect_output(\
                                    exe_path_map, collected_output, testcase)
            self.wrapper_obj.cleanup_logs(exe_path_map)

        return verdict, collected_output
    #~ def _execute_a_test()

    def _do_generate_tests (self, exe_path_map, code_builds_factory, \
                                                meta_criteria_tool_obj=None, \
                                                                max_time=None):
        dtl = self.code_builds_factory.repository_manager.get_dev_tests_list()
        ERROR_HANDLER.assert_true(dtl is not None, "invalid dev_test_list", \
                                                                    __file__)
        if os.path.isdir(self.tests_storage_dir):
            shutil.rmtree(self.tests_storage_dir)
        os.mkdir(self.tests_storage_dir)

        if self.wrapper_test_splitting:
            # Execute the tests with the counting wrapper
            logging.debug("## Splitting tests with wrapper")
            split_workdir = os.path.join(self.tests_storage_dir)
            new_exe_path_map = self.wrapper_obj.get_test_splitting_wrapper()\
                                    .set_wrapper(split_workdir, exe_path_map)
            sub_test_list = []
            for test in dtl:
                logging.debug('splitting test '+test) #DBG
                self.wrapper_obj.get_test_splitting_wrapper()\
                                            .switch_to_new_test()
                self.execute_testcase(test, new_exe_path_map, {})
                n_subtest, args = \
                                self.wrapper_obj.get_test_splitting_wrapper()\
                                                                .collect_data()
                for i in range(n_subtest):
                    sub_test_list.append([test+self.splittest_ext+str(i), \
                                        args[i] if i < len(args) else None])

            self.wrapper_obj.get_test_splitting_wrapper().cleanup()

            # update dtl with counter tests
            dtl = sub_test_list
        else:
            dtl = [[t, None] for t in dtl]

        common_fs.dumpJSON(dtl, self.test_list_storage_file)
        #ERROR_HANDLER.assert_true(os.path.isfile(self.test_list_storage_file))
    #~ def _do_generate_tests()
#~ class CustomTestcases
