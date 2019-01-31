
# This module is used through MetaTestcaseTool class
# Which access the relevant test case tools as specified
# The tools are organized by programming language
# For each language, there is a folder for each tool, 
# named after the tool in lowercase

# Each test case tool package have the following in the __init__.py file:
# import <Module>.<class extending BaseTestcaseTool> as TestcaseTool

from __future__ import print_function
import os, sys
import glob
import shutil

import muteria.common.matrices as common_matrices


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

    def get_checkpointer(self):
        return self.checkpointer

    def has_checkpointer(self):
        return self.checkpointer is not None

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

        return test_failed_verdicts


    def generate_tests (self, outputdir=None, code_builder_override=None):
        '''
        '''
        if outputdir is None:
            outputdir = self.tests_storage_dir
        if code_builder_override is None:
            code_builder_override = self.code_builder
        if os.path.isdir(outputdir):
            shutil.rmtree(outputdir)
        os.mkdir(outputdir)
        self.do_generate_tests (outputdir=outputdir, 
                                    code_builder=code_builder_override)

    @abc.abstractmethod
    def do_generate_tests (self, outputdir, code_builder)
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def prepare_code (self):
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def getTestsList(self):
        print ("!!! Must be implemented in child class !!!")

