#
# [LICENCE]
#
""" Testcase tool module. The class of interest is BaseTestcaseTool.
The class represent a testcase tool which manages a working directory
where, given code files(executable) represented in the repository dir,
corresponding tests are generated (harvested) by code files. Those test can
also be executed using the same code used to generate the tests or 
other code specified. 

The tools are organized by programming language

For each language, there is a folder for each tool, 
named after the tool in all lowercase , starting with letter or underscore(_),
The remaining caracters are either letter, number or underscore

XXX Each testcase tool package must make each test case tool visible in 
the __init__.py file (Just set to None if not defined).
For Example: 
- If nothing is defined:
>>> StaticTestcaseTool = None
>>> StaticMutantTestcaseTool = None
>>> DynamicTestcaseTool = None
>>> DynamicMutantTestcaseTool = None

- If  for example the StaticTestcaseTool is defined as the class 
<class extending BaseTestcaseTool>, in th module <Module>, replace
 "StaticTestcaseTool = None" with:
>>> import <Module>.<class extending BaseTestcaseTool> as StaticTestcaseTool

"""

from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import abc
import hashlib
import time
import multiprocessing
import joblib

import tqdm

import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

from muteria.drivers import DriversUtils

from muteria.drivers.checkpoint_handler import CheckPointHandler
from muteria.repositoryandcode.callback_object import DefaultCallbackObject

ERROR_HANDLER = common_mix.ErrorHandler

class BaseTestcaseTool(abc.ABC):
    '''
    '''

    def __init__(self, tests_working_dir, code_builds_factory, config, \
                                        head_explorer, checkpointer, \
                                        parent_meta_tool=None):
        # Set Constants
        self.compress_test_storage_dir = True

        # Set Direct Arguments Variables
        self.tests_working_dir = tests_working_dir
        self.code_builds_factory = code_builds_factory
        self.config = config
        self.head_explorer = head_explorer
        self.checkpointer = checkpointer
        self.parent_meta_tool = parent_meta_tool

        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.tests_working_dir is not None, \
                                    "Must specify tests_working_dir", __file__)

        # Set Indirect Arguments Variables
        ## Generate the tests into this folder (to be created by user)
        self.tests_storage_dir = os.path.join(
                        self.tests_working_dir, "tests_files")
        self.tests_storage_dir_archive = os.path.join(
                        self.tests_working_dir, "tests_files.tar.gz")
        self.custom_binary_dir = None
        if self.config.tool_user_custom is not None:
            self.custom_binary_dir = \
                        self.config.tool_user_custom.PATH_TO_TOOL_BINARY_DIR
            ERROR_HANDLER.assert_true(self.custom_binary_dir is None or \
                                    os.path.isdir(self.custom_binary_dir), \
                            "specified custom_binary_dir does not exist", \
                                                                    __file__)

        # Verify indirect Arguments Variables

        # Initialize Other Fields
        self.test_execution_time = {}
        self.test_execution_time_storage_file = os.path.join(\
                        self.tests_working_dir, "test_to_execution_time.json")
        self.shared_loc = multiprocessing.RLock()

        # Make Initialization Computation
        ## Create dirs
        if not os.path.isdir(self.tests_working_dir):
            self.clear_working_dir()

        if os.path.isfile(self.test_execution_time_storage_file):
            self.test_execution_time = common_fs.loadJSON(\
                                        self.test_execution_time_storage_file)

        # decompress potential test storage archive
        if self.compress_test_storage_dir:
            if os.path.isfile(self.tests_storage_dir_archive):
                if os.path.isdir(self.tests_storage_dir):
                    shutil.rmtree(self.tests_storage_dir)
                common_fs.TarGz.decompressDir(self.tests_storage_dir_archive)
    #~ def __init__()

    def __del__(self):
        # remove the decompressed the test storage dir
        if self.compress_test_storage_dir:
            if os.path.isfile(self.tests_storage_dir_archive) \
                                    and os.path.isdir(self.tests_storage_dir):
                shutil.rmtree(self.tests_storage_dir)
    #~ def __del__()

    def clear_working_dir(self):
        if os.path.isdir(self.tests_working_dir):
            shutil.rmtree(self.tests_working_dir)
        os.mkdir(self.tests_working_dir)
    #~ def clear_working_dir(self):

    def get_toolname(self):
        return self.config.get_tool_name()
    #~ def get_toolname()

    def get_toolalias(self):
        return self.config.get_tool_config_alias()
    #~ def get_toolalias()

    def get_checkpointer(self):
        return self.checkpointer
    #~ def get_checkpointer()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer(self)

    def execute_testcase (self, testcase, exe_path_map, env_vars, \
                                        timeout=None, \
                                        use_recorded_timeout_times=None, \
                                        recalculate_execution_times=False, \
                                        with_output_summary=True, \
                                        hash_outlog=True):
        return self._execute_testcase(testcase, exe_path_map, env_vars, \
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
        return self._runtests(testcases=testcases, exe_path_map=exe_path_map, \
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
                            
    class RepoRuntestsCallbackObject(DefaultCallbackObject):
        def after_command(self):
            # Copy the exes into the repo (user must revert)
            exe_path_map = self.post_callback_args[1]['exe_path_map']
            if self.post_callback_args[2]:
                self._copy_to_repo(exe_path_map, skip_none_dest=True)

            # execute
            res = self.post_callback_args[0](**self.post_callback_args[1])
            return res
    #~ class RepoRuntestsCallbackObject

    def _in_repo_execute_testcase(self, testcase, exe_path_map, env_vars, \
                                        timeout=None, \
                                        use_recorded_timeout_times=None, \
                                        recalculate_execution_times=False, \
                                        with_output_summary=True, \
                                        hash_outlog=True, \
                                        copy_exe_to_repo=True):
        callback_func = self._execute_testcase
        cb_obj = self.RepoRuntestsCallbackObject()
        cb_obj.set_post_callback_args((callback_func,
                                {
                                    "testcase": testcase,
                                    "exe_path_map": exe_path_map,
                                    "env_vars": env_vars,
                                    "timeout": timeout,
                                    "use_recorded_timeout_times":\
                                            use_recorded_timeout_times, \
                                    "recalculate_execution_times":\
                                            recalculate_execution_times, \
                                    "with_output_summary":with_output_summary,\
                                    "hash_outlog":hash_outlog,
                                }, copy_exe_to_repo))
        repo_mgr = self.code_builds_factory.repository_manager
        _, exec_verdict = repo_mgr.custom_read_access(cb_obj)
        # revert exes
        self.code_builds_factory.set_repo_to_build_default()
        return exec_verdict
    #~ def _in_repo_execute_testcase()

    def _in_repo_runtests(self, testcases, exe_path_map, env_vars, \
                                stop_on_failure=False, per_test_timeout=None, \
                                use_recorded_timeout_times=None, \
                                recalculate_execution_times=False, \
                                with_output_summary=True, hash_outlog=True, \
                                parallel_count=1, \
                                copy_exe_to_repo=True):
        callback_func = self._runtests
        cb_obj = self.RepoRuntestsCallbackObject()
        cb_obj.set_post_callback_args((callback_func,
                                {
                                    "testcases": testcases,
                                    "exe_path_map": exe_path_map,
                                    "env_vars": env_vars,
                                    "stop_on_failure": stop_on_failure,
                                    "per_test_timeout": per_test_timeout,
                                    "use_recorded_timeout_times":\
                                            use_recorded_timeout_times, \
                                    "recalculate_execution_times":\
                                            recalculate_execution_times, \
                                    "with_output_summary":with_output_summary,\
                                    "hash_outlog":hash_outlog, \
                                    "parallel_count": parallel_count,
                                }, copy_exe_to_repo))
        repo_mgr = self.code_builds_factory.repository_manager
        _, exec_verdicts = repo_mgr.custom_read_access(cb_obj)
        # revert exes
        self.code_builds_factory.set_repo_to_build_default()
        return exec_verdicts
    #~ def _in_repo_runtests()

    def _execute_testcase (self, testcase, exe_path_map, env_vars, \
                                        timeout=None, \
                                        use_recorded_timeout_times=None, \
                                        recalculate_execution_times=False, \
                                        with_output_summary=True, \
                                        hash_outlog=True):
        '''
        Execute a test case with the given executable and 
        say whether it failed

        :param testcase: string name of the test cases to execute
        :param exe_path_map: string representing the file system path to 
                        the executable to execute with the test
        :param env_vars: dict of environment variables to set before
                        executing the test ({<variable>: <value>})
        :returns: boolean failed verdict of the test 
                        (True if failed, False otherwise)
        '''

        if timeout is None:
            if use_recorded_timeout_times is not None:
                ERROR_HANDLER.assert_true(use_recorded_timeout_times > 0, \
                                        "use_recorded_timeout_times must be "
                                        "positive if not None", __file__)
                if testcase in self.test_execution_time:
                    timeout = self.test_execution_time[testcase] * \
                                                use_recorded_timeout_times
        else:
            ERROR_HANDLER.assert_true(use_recorded_timeout_times is None, \
                                "use_recorded_timeout_times must not be set "
                                "when timeout is not None", __file__)


        self._prepare_executable(exe_path_map, env_vars, \
                                            collect_output=with_output_summary)
        self._set_env_vars(env_vars)

        start_time = time.time()
        fail_verdict, execoutlog_hash = \
                        self._oracle_execute_a_test(testcase, exe_path_map, \
                                            env_vars, timeout=timeout, \
                                    with_output_summary=with_output_summary, \
                                                    hash_outlog=hash_outlog)

        # Record exec time if not existing
        if recalculate_execution_times:
            self.test_execution_time[testcase] = \
                                        1 + int(time.time() - start_time)

        self._restore_env_vars()
        self._restore_default_executable(exe_path_map, env_vars, \
                                            collect_output=with_output_summary)

        return fail_verdict, execoutlog_hash
    #~ def _execute_testcase()

    def _runtests(self, testcases, exe_path_map, env_vars, \
                                stop_on_failure=False, per_test_timeout=None, \
                                use_recorded_timeout_times=None, \
                                recalculate_execution_times=False, \
                                with_output_summary=True, hash_outlog=True, \
                                parallel_count=1):
        '''
        Execute the list of test cases with the given executable and 
        say, for each test case, whether it failed.
        Note: Re-implement this if there the tool implements ways to faster
        execute multiple test cases.

        :param testcases: list of test cases to execute
        :param exe_path_map: string representing the file system path to 
                        the executable to execute with the tests
        :param env_vars: dict of environment variables to set before
                        executing each test ({<variable>: <value>})
        :param stop_on_failure: decide whether to stop the test execution once
                        a test fails
        :returns: plitair of:
                - dict of testcase and their failed verdict.
                 {<test case name>: <True if failed, False if passed, 
                    UNCERTAIN_TEST_VERDICT if uncertain>}
                 If stop_on_failure is True, only return the tests that have 
                 been executed until the failure
                - test execution output log hash data object or None
        '''
        # @Checkpoint: create a checkpoint handler (for time)
        checkpoint_handler = CheckPointHandler(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            logging.warning("{} {} {}".format( \
                            "The function 'runtests' is finished according", \
                            "to checkpoint, but called again. None returned", \
                            "\nPlease Confirm reexecution..."))
            if common_mix.confirm_execution("{} {}".format( \
                                "Function 'runtests' is already", \
                                "finished, do yo want to restart?")):
                checkpoint_handler.restart()
                logging.info("Restarting the finished 'runtests'")
            else:
                ERROR_HANDLER.error_exit(err_string="{} {} {}".format( \
                        "Execution halted. Cannot continue because no value", \
                        " can be returned. Check the results of the", \
                        "finished execution"), call_location=__file__)

        if per_test_timeout is None:
            per_test_timeout = {tc: None for tc in testcases}
            if use_recorded_timeout_times is not None:
                ERROR_HANDLER.assert_true(use_recorded_timeout_times > 0, \
                                        "use_recorded_timeout_times must be "
                                        "positive if not None", __file__)
                per_test_timeout.update({x: (y * use_recorded_timeout_times) \
                                for x, y in self.test_execution_time.items()})
        else:
            ERROR_HANDLER.assert_true(use_recorded_timeout_times is None, \
                                "use_recorded_timeout_times must not be set "
                                "when per_test_timeout is set", __file__)

        # Prepare the exes
        self._prepare_executable(exe_path_map, env_vars, \
                                            collect_output=with_output_summary)
        self._set_env_vars(env_vars)

        test_failed_verdicts = {} 
        test_outlog_hash = {} 
        processbar = tqdm.tqdm(testcases, leave=False, dynamic_ncols=True) 

        # Parallel stuffs
        ptest_tresh = 5

        def test_exec_iteration(testcase):
            processbar.set_description("Running Test %s"% testcase)
            start_time = time.time()
            test_failed, execoutlog_hash = \
                        self._oracle_execute_a_test(testcase, exe_path_map, \
                                        env_vars, \
                                        timeout=per_test_timeout[testcase], \
                                    with_output_summary=with_output_summary, \
                                        hash_outlog=hash_outlog)
            
            # Record exec time if not existing
            with self.shared_loc:
                if recalculate_execution_times:
                    self.test_execution_time[testcase] = \
                                            1 + int(time.time() - start_time)

                test_failed_verdicts[testcase] = test_failed
                test_outlog_hash[testcase] = execoutlog_hash
            return test_failed
        #~ def test_exec_iteration()

        if self.can_run_tests_in_parallel() and len(testcases) >= ptest_tresh \
                            and (parallel_count is None or parallel_count > 1):
            if parallel_count is None:
                paralle_count = min(len(testcases), \
                                                multiprocessing.cpu_count())
            else:
                paralle_count = min(len(testcases), parallel_count)
            joblib.Parallel(n_jobs=paralle_count, require='sharedmem')\
                            (joblib.delayed(test_exec_iteration)(testcase) \
                                                for testcase in processbar)
        else:
            for testcase in processbar: 
                test_failed = test_exec_iteration(testcase)
                if stop_on_failure and test_failed != \
                                common_mix.GlobalConstants.PASS_TEST_VERDICT:
                    break
        
        if recalculate_execution_times:
            common_fs.dumpJSON(self.test_execution_time, \
                            self.test_execution_time_storage_file, pretty=True)

        # Restore back the exes
        self._restore_env_vars()
        self._restore_default_executable(exe_path_map, env_vars, \
                                            collect_output=with_output_summary)

        if stop_on_failure:
            # Make sure the non executed test has the uncertain value (None)
            if len(test_failed_verdicts) < len(testcases):
                for testcase in set(testcases) - set(test_failed_verdicts):
                    test_failed_verdicts[testcase] = \
                            common_mix.GlobalConstants.UNCERTAIN_TEST_VERDICT
                    test_outlog_hash[testcase] = common_matrices.\
                                        OutputLogData.UNCERTAIN_TEST_OUTLOGDATA

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished(None)

        if not with_output_summary:
            test_outlog_hash = None

        return test_failed_verdicts, test_outlog_hash
    #~ def _runtests()

    def _oracle_execute_a_test (self, testcase, exe_path_map, env_vars, \
                                        callback_object=None, timeout=None,
                                with_output_summary=True, hash_outlog=True):
        """ Execute a test and use the specified oracles to check
            Also collect the output

            :param hash_outlog: (bool) Choose to hash or not at runtime 
                                (flakiness check)
        """

        if timeout is None:
            timeout = self.config.ONE_TEST_EXECUTION_TIMEOUT
        
        #logging.debug(str(timeout))
        verdict, output_err = self._execute_a_test(\
                                            testcase,exe_path_map, env_vars,\
                                            callback_object=callback_object, \
                                            timeout=timeout, \
                                            collect_output=with_output_summary)
        if with_output_summary:
            retcode, outlog, timedout = output_err
            out_len = len(outlog)
            if hash_outlog:
                outlog = outlog.encode('utf-8', 'backslashreplace')
                out_hash_val = hashlib.sha512(outlog).hexdigest()
            else:
                out_hash_val = outlog
            outlog_summary = {
                common_matrices.OutputLogData.OUTLOG_LEN: out_len,
                common_matrices.OutputLogData.OUTLOG_HASH: out_hash_val,
                common_matrices.OutputLogData.RETURN_CODE: retcode,
                common_matrices.OutputLogData.TIMEDOUT: timedout,
            }
        else:
            outlog_summary = None

        return verdict, outlog_summary
    #~ def _oracle_execute_a_test()

    def generate_tests (self, exe_path_map, \
                            meta_criteria_tool_obj=None, \
                            parallel_count=1, \
                            code_builds_factory_override=None, max_time=None):
        '''
        '''

        logging.debug("# Generating tests with {} ...".format(\
                                        self.config.get_tool_config_alias()))

        # @Checkpoint: create a checkpoint handler (for time)
        checkpoint_handler = CheckPointHandler(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        outputdir = self.tests_storage_dir
        if code_builds_factory_override is None:
            code_builds_factory_override = self.code_builds_factory
        if os.path.isdir(outputdir):
            shutil.rmtree(outputdir)

        # If compressing test storage dir, remove archive if working on 
        # the default test storage dir
        if self.compress_test_storage_dir \
                                and not os.path.isdir(self.tests_storage_dir):
            if os.path.isfile(self.tests_storage_dir_archive):
                os.remove(self.tests_storage_dir_archive)

        os.mkdir(outputdir)
        self._do_generate_tests (exe_path_map, \
                            code_builds_factory=code_builds_factory_override, \
                            meta_criteria_tool_obj=meta_criteria_tool_obj, \
                                                            max_time=max_time)


        # Compress test storage dir?
        if self.compress_test_storage_dir:
            if os.path.isdir(self.tests_storage_dir):
                common_fs.TarGz.compressDir(self.tests_storage_dir, \
                                            self.tests_storage_dir_archive, \
                                            remove_in_directory=False)

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished(None)
    #~ def generate_tests()

    def _set_env_vars(self, env_vars):
        if env_vars:
            try:
                if self.env_vars_store is not None:
                    ERROR_HANDLER.error_exit(\
                            "Bug: env_var set again without restore", __file__)
            except AttributeError:
                pass
            self.env_vars_store = os.environ.copy()
            os.environ.update(env_vars)
        else:
            self.env_vars_store = os.environ
    #~ def _set_env_vars()

    def _restore_env_vars(self):
        try:
            if self.env_vars_store is None:
                raise AttributeError
        except AttributeError:
            ERROR_HANDLER.error_exit("restoring unset env")
        os.environ = self.env_vars_store
        self.env_vars_store = None
    #~ def _restore_env_vars()

    def tool_installed (self):
        """ Check that a tool with given conf is installed
        """
        return self.installed(custom_binary_dir=self.custom_binary_dir)
    #~ def tool_installed ()

    def _dir_chmod777(self, dirpath):
        try:
            for root_, dirs_, files_ in os.walk(dirpath):
                for sub_d in dirs_:
                    os.chmod(os.path.join(root_, sub_d), 0o777)
                for f_ in files_:
                    os.chmod(os.path.join(root_, f_), 0o777)
        except PermissionError:
            ret,out,_ = DriversUtils.execute_and_get_retcode_out_err('sudo', \
                                            ['chmod', '777', '-R', dirpath])
            ERROR_HANDLER.assert_true(ret == 0, \
                        "'sudo chmod 777 -R "+dirpath+"' failed (returned "+\
                                        str(ret)+"), error: "+out, __file__)
    #~ def _dir_chmod777()

    def requires_criteria_instrumented(self):
        return False
    #~ def requires_criteria_instrumented()

    def can_run_tests_in_parallel(self):
        return False
    #~ def can_run_tests_in_parallel()

    #######################################################################
    ##################### Methods to implement ############################
    #######################################################################

    @classmethod
    @abc.abstractclassmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def installed()

    @abc.abstractmethod
    def get_testcase_info_object(self):
        print ("!!! Must be implemented in child class !!!")
    #~ def get_testcase_info_object()

    @abc.abstractmethod
    def _prepare_executable (self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Make sure we have the right executable ready (if needed)
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def _prepare_executale()

    @abc.abstractmethod
    def _restore_default_executable(self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Restore back the default executable (if needed).
            Useful for test execution that require the executable
            at a specific location.
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def _restore_default_executable()

    @abc.abstractmethod
    def _execute_a_test (self, testcase, exe_path_map, env_vars, \
                    callback_object=None, timeout=None, collect_output=None):
        """ Execute a test given that the executables have been set 
            properly
        """
    #~ def _execute_a_test()

    @abc.abstractmethod
    def _do_generate_tests (self, exe_path_map, code_builds_factory, 
                                        meta_criteria_tool_obj=None, \
                                        max_time=None):
        print ("!!! Must be implemented in child class !!!")
    #~ def _do_generate_tests()
#~ class BaseTestcaseTool