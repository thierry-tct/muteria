
# This module is used through MetaTestcaseTool class
# Which access the relevant testcase tools as specified

# The tools are organized by programming language
# For each language, there is a folder for each tool, 
# named after the tool in lowercase

# Each testcase tool package have the following in the __init__.py file:
# import <Module>.<class extending BaseTestcaseTool> as TestcaseTool

from __future__ import print_function
import os
import sys
import glob
import copy
import logging

import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from base_testcasetool import BaseTestcaseTool

from ... import ToolsModulesLoader

from ...checkpoint_handler import CheckpointHandlerForMeta

ERROR_HANDLER = common_mix.ErrorHandler

class MetaTestcaseTool(object):
    ''' 
    '''

    UNCERTAIN_TEST_VERDICT = common_mix.GlobalConstants.UNCERTAIN_TEST_VERDICT

    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"

    # The Fault execution matrix has a unique key represented by this string
    FAULT_MATRIX_KEY = "fault_revealed"

    def __init__(self, language, tests_working_dir, code_builds_factory,
                                                    test_tool_config_list):

        """ Initialize a meta testcase tool object.
        :type language:
        :param language:

        :type tests_working_dir:
        :param tests_working_dir:

        :type code_builds_factory:
        :param code_builds_factory:

        :type test_tool_config_list:
        :param test_tool_config_list:

        :raises:

        :rtype:
        """
        # Set Constants
        self.modules_dict = ToolsModulesLoader.get_tools_modules( \
                                            ToolsModulesLoader.TESTCASES_TOOLS)

        # Set Direct Arguments Variables
        self.language = language
        self.tests_working_dir = tests_working_dir
        self.code_builds_factory = code_builds_factory
        self.test_tool_config_list = test_tool_config_list

        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.tests_working_dir is None, \
                                    "Must specify tests_working_dir", __FILE__)
        ERROR_HANDLER.assert_true(len(self.test_tool_config_list) != \
                                        len(set(self.test_tool_config_list), \
                        "some tool configs appear multiple times", __FILE__))

        # Set Indirect Arguments Variables
        self.checkpoints_dir = os.path.join(self.tests_working_dir, \
                                                            "_checkpoints_")
        self.testcases_info_file = \
                os.path.join(self.tests_working_dir, "testcasesInfos.json")
        # Verify Indirect Arguments Variables

        # Initialize other Fields
        self.testcases_tools = {}
        self.checkpointer = None 

        # Make Initialization Computation ()
        ## Create dirs
        if not os.path.isdir(self.tests_working_dir):
            os.mkdir(self.tests_working_dir)

        if not os.path.isdir(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)

        # Set the checkpointer
        self.checkpointer = common_fs.CheckpointState(\
                                                *self._get_checkpoint_files())

        # Create the diffent tools
        for idx in range(len(test_tool_config_list)):
            toolname = test_tool_config_list[idx].get_tool_name()
            tool_working_dir = self._get_test_tool_out_folder(toolname)
            config = config_list[idx]
            tool_checkpointer = common_fs.CheckpointState(\
                            *self._get_test_tool_checkpoint_files(toolname))
            self.checkpointer.add_dep_checkpoint_state(tool_checkpointer)
            self.testcases_tools[toolname] = {
                self.TOOL_OBJ_KEY: self._create_testcase_tool(toolname, \
                                                    tool_working_dir, config, \
                                                    tool_checkpointer),
                self.TOOL_WORKDIR_KEY: tool_working_dir,
            }
    #~ def __init__()

    def _create_testcase_tool(self, toolname, tool_working_dir, \
                                                    config, tool_checkpointer):
        '''
            Each tool module must have the function createTestcaseTool() 
            implemented
        '''
        testcase_tool = \
                    self.modules_dict[self.language][toolname].TestcaseTool( \
                                            tool_working_dir, \
                                            self.code_builds_factory, \
                                            config, \
                                            tool_checkpointer)
        return testcase_tool
    #~ def _create_testcase_tool()


    def execute_testcase (self, meta_testcase, exe_path, env_vars):
        '''
        Execute a test case with the given executable and 
        say whether it failed

        :param meta_testcase: string name of the test cases to execute
        :param exe_path: string representing the file system path to 
                        the executable to execute with the test
        :param env_vars: dict of environment variables to set before
                        executing the test ({<variable>: <value>})
        :returns: boolean failed verdict of the test 
                        (True if failed, False otherwise)
        '''
        
        # Find which test tool's the testcase is, then execute
        ttoolname, testcase = self.reverse_meta_testcase(meta_testcase)
        if ttoolname not in testcases_tools:
            logging.error("Test tool {} not registered".format(ttoolname))
            ERROR_HANDLER.error_exit_file(__file__)
        ttool = self.testcases_tools[ttoolname][self.TOOL_OBJ_KEY]
        return ttool.execute_testcase(testcase, exe_path, env_vars)
    #~ def execute_testcase()

    def runtests(self, meta_testcases, exe_path, env_vars, \
                    stop_on_failure=False, fault_test_execution_matrix=None):
        '''
        Execute the list of test cases with the given executable and 
        say, for each test case, whether it failed

        :param meta_testcases: list of test cases to execute
        :param exe_path: string representing the file system path to 
                        the executable to execute with the tests
        :param env_vars: dict of environment variables to set before
                        executing each test ({<variable>: <value>})
        :param stop_on_failure: decide whether to stop the test 
                        execution once a test fails
        :param fault_test_execution_matrix: Optional matrix to store the 
                        tests' pass fail execution data
        :returns: dict of testcase and their failed verdict.
                 {<test case name>: <True if failed, False if passed,
                    UNCERTAIN_TEST_VERDICT if uncertain>}
                 If stop_on_failure is True, only return the tests that 
                 have been executed until the failure
        '''
        
        # @Checkpoint: create a checkpoint handler
        cp_func_name = "runtests"
        cp_task_id = 1
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

        # @Checkpoint: Get the saved payload (data kapt for each tool)
        meta_test_failed_verdicts = checkpoint_handler.get_optional_payload()
        if meta_test_failed_verdicts is None:
            meta_test_failed_verdicts = {} 

        # Make sure the tests are unique
        assert len(meta_testcases) == len(set(meta_testcases)), \
                                                    "not all tests are unique"

        testcases_by_tool = {}
        for meta_testcase in meta_testcases:
            ttoolname, testcase = self.reverse_meta_testcase(meta_testcase)
            if ttoolname not in testcases_by_tool:
                testcases_by_tool[ttoolname] = []
            testcases_by_tool[ttoolname].append(testcase)
            
        found_a_failure = False
        for tpos, ttoolname in enumerate(testcases_by_tool.keys()):
            # @Checkpoint: Check whether already executed
            if not checkpoint_handler.is_to_execute(func_name=cp_func_name, \
                                                taskid=cp_task_id, \
                                                tool=ttoolname):
                continue

            # Actual execution
            ttool = self.testcases_tools[ttoolname][self.TOOL_OBJ_KEY]
            test_failed_verdicts = ttool.runtests( \
                                                testcases_by_tool[ttoolname], \
                                                exe_path, env_vars, \
                                                stop_on_failure)
            for testcase in test_failed_verdicts:
                meta_testcase = make_meta_testcase(testcase, ttoolname)
                meta_test_failed_verdicts[meta_testcase] = \
                                                test_failed_verdicts[testcase]
                if test_failed_verdicts[testcase == True]:
                    found_a_failure = True

            # @Checkpoint: Chekpointing
            checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ttoolname, \
                                        opt_payload=meta_test_failed_verdicts)

            if stop_on_failure and found_a_failure:
                # @Checkpoint: Chekpointing for remaining tools
                for rem_tool in testcases_by_tool.keys()[tpos+:]:
                    checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=rem_tool, \
                                        opt_payload=meta_test_failed_verdicts)
                break
                                        
        if stop_on_failure:
            # Make sure the non executed test has the uncertain value (None)
            if len(meta_test_failed_verdicts) < len(meta_testcases):
                for meta_testcase in meta_testcases:
                    meta_test_failed_verdicts[meta_testcase] = \
                                                self.UNCERTAIN_TEST_VERDICT
                    
        assert len(meta_test_failed_verdicts) == len(meta_testcases), \
                    "Not all tests have a verdict reported"

        if fault_test_execution_matrix is not None:
            assert fault_test_execution_matrix.is_empty(), \
                                                "matrix must be empty"
            failverdict2val = {
                True: fault_test_execution_matrix.getActiveCellDefaultVal(),
                False: fault_test_execution_matrix.getInactiveCellVal(),
                self.UNCERTAIN_TEST_VERDICT: \
                    fault_test_execution_matrix.getUncertainCellDefaultVal()
            }
            cells_dict = {}
            for meta_testcase in meta_test_failed_verdicts
                cells_dict[meta_testcase] = \
                    failverdict2val[meta_test_failed_verdicts[meta_testcase]]

            fault_test_execution_matrix.add_row_by_key(self.FAULT_MATRIX_KEY, \
                                                cells_dict, serialize=True)

        # @Checkpoint: Finished
        detailed_exectime = {tt: tt.get_checkpointer().get_execution_time() \
                                            for tt in testcases_by_tool.keys()}
        checkpoint_handler.set_finished( \
                                    detailed_exectime_obj=detailed_exectime)

        return meta_test_failed_verdicts
    #~ def runtests()

    def generate_tests (self):
        # @Checkpoint: create a checkpoint handler
        cp_func_name = "generate_tests"
        cp_task_id = 1
        checkpoint_handler = CheckpointHandlerForMeta(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        # Generate
        for ttoolname in self.testcases_tools:
            # Check whether already executed
            if checkpoint_handler.is_to_execute(func_name=cp_func_name, \
                                                taskid=cp_task_id, \
                                                tool=ttoolname)

                # Actual Execution
                ttool = self.testcases_tools[ttoolname][self.TOOL_OBJ_KEY]
                ttool.generate_tests()

                # @Checkpoint: Checkpointing
                checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                                taskid=cp_task_id, \
                                                tool=ttoolname)

        # Compute testcases info
        meta_testcase_info_obj = {}
        for ttoolname in self.testcases_tools:
            ttool = self.testcases_tools[ttoolname][self.TOOL_OBJ_KEY]
            tool_testcase_info = ttool.get_testcase_info_object()
            for t_test in tool_testcase_info:
                meta_t_key = self.make_meta_testcase(t_test, ttoolname)
                assert meta_t_key not in meta_testcase_info_obj, \
                                                "Key already existing (BUG)"
                meta_testcase_info_obj[meta_t_key] = tool_testcase_info[t_test]
        self._store_testcase_info_to_file(meta_testcase_info_obj)

        # @Checkpoint: Finished
        detailed_exectime = {tt: tt.get_checkpointer().get_execution_time() \
                                                for tt in self.testcases_tools}
        checkpoint_handler.set_finished( \
                                    detailed_exectime_obj=detailed_exectime)
    #~ def generate_tests()
    
    def make_meta_testcase(testname, toolname):
        return ":".join([toolname, testname])
    #~ def make_meta_testcase()

    def reverse_meta_testcase(meta_testcase, toolname):
        parts = meta_testcase.split(':', 1)
        assert len(parts) >= 2, "invalibd meta testcase"
        toolname, testcase = parts
        return toolname, testcase
    #~ def reverse_meta_testcase()

    def get_testcase_info_object(self):
        return common_fs.loadJSON(self.get_testcase_info_file())
    #~ def get_testcase_info_object()

    def _store_testcase_info_to_file(self, data_object):
        common_fs.dumpJSON(data_object, self.get_testcase_info_file())
    #~ def _store_testcase_info_to_file()

    def get_testcase_info_file(self):
        return self.testcases_info_file
    #~ def get_testcase_info_file()

    def _get_test_tool_out_folder(test_toolname, top_outdir=None):
        if top_outdir is None:
            top_outdir = self.tests_working_dir
        return os.path.join(top_outdir, test_toolname)
    #~ def _get_test_tool_out_folder()

    def _get_test_tool_checkpoint_files(self, test_toolname, \
                                                    top_checkpoint_dir=None):
        if top_checkpoint_dir is None:
            top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                            test_toolname+"_checkpoint.state"+suffix) \
                            for suffix in ("", ".backup")]
    #~ def _get_test_tool_checkpoint_files()
        
    def _get_checkpoint_files(self):
        top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                        "checkpoint.state"+suffix) \
                        for suffix in ("", ".backup")]
    #~ def _get_checkpoint_files()

    def get_checkpoint_state_object(self):
        return self.checkpointer
    #~ def get_checkpoint_state_object()

    def has_checkpointer(self):
        return self.checkpointer is not None
#~ class MetaTestcaseTool
