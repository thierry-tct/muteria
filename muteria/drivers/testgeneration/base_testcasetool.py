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

import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from muteria.drivers.checkpoint_handler import CheckPointHandler

ERROR_HANDLER = common_mix.ErrorHandler

class BaseTestcaseTool(abc.ABC):
    '''
    '''

    UNCERTAIN_TEST_VERDICT = common_mix.GlobalConstants.UNCERTAIN_TEST_VERDICT
    PASS_TEST_VERDICT = common_mix.GlobalConstants.PASS_TEST_VERDICT
    FAIL_TEST_VERDICT = common_mix.GlobalConstants.FAIL_TEST_VERDICT

    def __init__(self, tests_working_dir, code_builds_factory, config, \
                                                                checkpointer):
        # Set Constants

        # Set Direct Arguments Variables
        self.tests_working_dir = tests_working_dir
        self.code_builds_factory = code_builds_factory
        self.config = config
        self.checkpointer = checkpointer

        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.tests_working_dir is None, \
                                    "Must specify tests_working_dir", __file__)

        # Set Indirect Arguments Variables
        ## Generate the tests into this folder (to be created by user)
        self.tests_storage_dir = os.path.join(
                        self.tests_working_dir, "tests_files")

        # Verify indirect Arguments Variables

        # Initialize Other Fields

        # Make Initialization Computation
        ## Create dirs
        if not os.path.isdir(self.tests_working_dir):
            os.mkdir(self.tests_working_dir)
    #~ def __init__()

    def get_checkpointer(self):
        return self.checkpointer
    #~ def get_checkpointer()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer(self)

    @abc.abstractmethod
    def _prepare_executable (self, exe_path_map, env_vars):
        """ Make sure we have the right executable ready (if needed)
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def _prepare_executale()

    @abc.abstractmethod
    def _restore_default_executable(self, exe_path_map, env_vars):
        """ Restore back the default executable (if needed)
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def _restore_default_executable()

    @abc.abstractclassmethod
    def _execute_a_test (self, testcase, exe_path_map, env_vars):
        """ Execute a test given that the executables have been set 
            properly
        """
    #~ def _execute_a_test()

    def execute_testcase (self, testcase, exe_path_map, env_vars):
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
        self._prepare_executable(exe_path_map,env_vars)
        fail_verdict = self._execute_a_test(testcase, exe_path_map,env_vars)
        self._restore_default_executable(exe_path_map,env_vars)

        return fail_verdict
    #~ def execute_testcase()

    def runtests(self, testcases, exe_path_map, env_vars, \
                                stop_on_failure=False, parallel_count=1):
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
        :returns: dict of testcase and their failed verdict.
                 {<test case name>: <True if failed, False if passed, 
                    UNCERTAIN_TEST_VERDICT if uncertain>}
                 If stop_on_failure is True, only return the tests that have 
                 been executed until the failure
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

        # Prepare the exes
        self._prepare_executable(exe_path_map,env_vars)

        test_failed_verdicts = {} 
        for testcase in testcases:
            test_failed = self._execute_a_test( \
                                            testcase, exe_path_map, env_vars)
            test_failed_verdicts[testcase] = test_failed
            if stop_on_failure and test_failed:
                break
        # Restore back the exes
        self._restore_default_executable(exe_path_map,env_vars)

        if stop_on_failure:
            # Make sure the non executed test has the uncertain value (None)
            if len(test_failed_verdicts) < len(testcases):
                for testcase in set(testcases) - set(test_failed_verdicts):
                    test_failed_verdicts[testcase] = \
                                                    self.UNCERTAIN_TEST_VERDICT

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished(None)

        return test_failed_verdicts
    #~ def runtests()

    def generate_tests (self, exe_path_map, parallel_count=1, outputdir=None, \
                                            code_builds_factory_override=None):
        '''
        '''
        # @Checkpoint: create a checkpoint handler (for time)
        checkpoint_handler = CheckPointHandler(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        if outputdir is None:
            outputdir = self.tests_storage_dir
        if code_builds_factory_override is None:
            code_builds_factory_override = self.code_builds_factory
        if os.path.isdir(outputdir):
            shutil.rmtree(outputdir)
        os.mkdir(outputdir)
        self._do_generate_tests (exe_path_map, outputdir=outputdir, \
                            code_builds_factory=code_builds_factory_override)

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished(None)
    #~ def generate_tests()

    @abc.abstractmethod
    def _do_generate_tests (self, exe_path_map, outputdir, \
                                                        code_builds_factory):
        print ("!!! Must be implemented in child class !!!")
    #~ def _do_generate_tests()

    @abc.abstractmethod
    def prepare_code (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def prepare_code()

    @abc.abstractmethod
    def get_testcase_info_object(self):
        print ("!!! Must be implemented in child class !!!")
    #~ def getTestsList()
