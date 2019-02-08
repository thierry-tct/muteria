
# The tools are organized by programming language

# For each language, there is a folder for each tool, 
# named after the tool in all lowercase , starting with letter or underscore(_),
# The remaining caracters are either letter, number or underscore


# XXX Each testcase tool package must have the 
# following in the __init__.py file:
# import <Module>.<class extending BaseTestcaseTool> as TestcaseTool

from __future__ import print_function
import os, sys
import glob
import shutil
import logging

import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class BaseTestcaseTool(object):
    '''
    '''

    UNCERTAIN_TEST_VERDICT = None

    def __init__(self, tests_working_dir, code_builder, config, checkpointer):
        sefl.tests_working_dir = tests_working_dir
        self.code_builder = code_builder
        self.config = config
        self.checkpointer = checkpointer

        if self.tests_working_dir is not None:
            if not os.path.isdir(self.tests_working_dir):
                os.mkdir(self.tests_working_dir)

        # Generate the tests into this folder (to be created by user)
        self.tests_storage_dir = os.path.join(
                        self.tests_working_dir, "tests_files")
    #~ def __init__()

    def get_checkpointer(self):
        return self.checkpointer
    #~ def get_checkpointer()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer(self)

    @abc.abstractmethod
    def execute_testcase (self, testcase, exe_path, env_vars):
        '''
        Execute a test case with the given executable and 
        say whether it failed

        :param testcase: string name of the test cases to execute
        :param exe_path: string representing the file system path to 
                        the executable to execute with the test
        :param env_vars: dict of environment variables to set before
                        executing the test ({<variable>: <value>})
        :returns: boolean failed verdict of the test 
                        (True if failed, False otherwise)
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def execute_testcase()

    def runtests(self, testcases, exe_path, env_vars, stop_on_failure=False):
        '''
        Execute the list of test cases with the given executable and 
        say, for each test case, whether it failed.
        Note: Re-implement this if there the tool implements ways to faster
        execute multiple test cases.

        :param testcases: list of test cases to execute
        :param exe_path: string representing the file system path to 
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
        checkpoint_handler = CheckpointHandlerForMeta(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            logging.warning("%s %s" %("The function 'runtests' is finished", \
                    "according to checkpoint, but called again. None returned")
            if common_mix.confirm_execution("%s %s" % ( \
                                "Function 'runtests' is already", \
                                "finished, do yo want to restart?")):
                checkpoint_handler.restart()
                logging.info("Restarting the finished 'runtests'")
            else:
                ERROR_HANDLER.error_exit_file(__file__, \
                        err_string="%s %s %s" % ("Execution halted. Cannot", \
                        "continue because no value can be returned. Check", \
                        "the results of the finished execution"))

        test_failed_verdicts = {} 
        for testcase in testcases:
            test_failed = self.execute_testcase(testcase, exe_path, env_vars)
            test_failed_verdicts[testcase] = test_failed
            if stop_on_failure and test_failed:
                break

        if stop_on_failure:
            # Make sure the non executed test has the uncertain value (None)
            if len(test_failed_verdicts) < len(testcases):
                for testcase in set(testcases) - set(test_failed_verdicts):
                    test_failed_verdicts[testcase] = UNCERTAIN_TEST_VERDICT

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished()

        return test_failed_verdicts
    #~ def runtests()

    def generate_tests (self, outputdir=None, code_builder_override=None):
        '''
        '''
        # @Checkpoint: create a checkpoint handler (for time)
        checkpoint_handler = CheckpointHandlerForMeta(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        if outputdir is None:
            outputdir = self.tests_storage_dir
        if code_builder_override is None:
            code_builder_override = self.code_builder
        if os.path.isdir(outputdir):
            shutil.rmtree(outputdir)
        os.mkdir(outputdir)
        self._do_generate_tests (outputdir=outputdir, 
                                    code_builder=code_builder_override)

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished()
    #~ def generate_tests()

    @abc.abstractmethod
    def _do_generate_tests (self, outputdir, code_builder)
        print ("!!! Must be implemented in child class !!!")
    #~ def _do_generate_tests()

    @abc.abstractmethod
    def prepare_code (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def prepare_code()

    @abc.abstractmethod
    def getTestsList(self):
        print ("!!! Must be implemented in child class !!!")
    #~ def getTestsList()
