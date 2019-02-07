
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

ERROR_HANDLER = common_mix.ErrorHandler()

class MetaTestcaseTool(object):
    ''' 
    '''

    UNCERTAIN_TEST_VERDICT = BaseTestcaseTool.UNCERTAIN_TEST_VERDICT

    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"

    # The Fault execution matrix has a unique key represented by this string
    FAULT_MATRIX_KEY = "fault_revealed"

    def __init__(self, tests_working_dir,
                        code_builder,
                        language, 
                        tests_toolname_list, 
                        config_list):
        self.modules_dict = ToolsModulesLoader.get_tools_modules(
                                    ToolsModulesLoader.TESTCASES_TOOLS)
        if len(tests_toolname_list) != len(config_list):
            logging.error("mismatch between tools and config"}
            ERROR_HANDLER.error_exit()

        if len(tests_toolname_list) != len(set(tests_toolname_list)):
            logging.error("some tools appear multiple times")
            ERROR_HANDLER.error_exit()

        self.tests_working_dir = tests_working_dir
        self.code_builder = code_builder

        if self.tests_working_dir is not None:
            if not os.path.isdir(self.tests_working_dir):
                os.mkdir(self.tests_working_dir)
        else:
            logging.error("Must specify tests_working_dir")
            ERROR_HANDLER.error_exit()

        self.checkpoints_dir = os.path.join(self.tests_working_dir, \
                                                            "_checkpoints_")
        if not os.path.isdir(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)

        self.checkpointer = common_fs.CheckpointState(\
                                                *self.get_checkpoint_files())

        self.testcases_info_file = \
                os.path.join(self.tests_working_dir, "testcasesInfos.json")

        self.testcases_tools = {}
        for idx in range(len(tests_toolname_list)):
            toolname = tests_toolname_list[idx]
            tool_working_dir = self.get_test_tool_out_folder(toolname)
            config = config_list[idx]
            tool_checkpointer = common_fs.CheckpointState(\
                            *self.get_mutation_tool_checkpoint_files(toolname))
            self.checkpointer.add_dep_checkpoint_state(tool_checkpointer)
            self.testcases_tools[toolname] = {
                self.TOOL_OBJ_KEY: self.get_testcase_tool(language, toolname, \
                                                    tool_working_dir, config, \
                                                    tool_checkpointer),
                self.TOOL_WORKDIR_KEY: tool_working_dir,
            }
    #~ def __init__()

    def get_testcase_tool(self, language, toolname, tool_working_dir, \
                                                    config, tool_checkpointer):
        '''
            Each tool module must have the function createTestcaseTool() 
            implemented
        '''
        testcase_tool = self.modules_dict[language][toolname].TestcaseTool(
                                            tool_working_dir,
                                            self.code_builder,
                                            config,
                                            tool_checkpointer)
        return testcase_tool
    #~ def get_testcase_tool()


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
        assert len(meta_testcases) == len(set(meta_testcases)), "not all tests are unique"

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
                meta_testcase = get_meta_column(testcase, ttoolname)
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
        checkpoint_handler.set_finished(detailed_exectime_obj=detailed_exectime)

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
                meta_t_key = self.get_meta_column(t_test, ttoolname)
                assert meta_t_key not in meta_testcase_info_obj, \
                                                "Key already existing (BUG)"
                meta_testcase_info_obj[meta_t_key] = tool_testcase_info[t_test]
        self.storeTestcaseInfoToFile(meta_testcase_info_obj)

        # @Checkpoint: Finished
        detailed_exectime = {tt: tt.get_checkpointer().get_execution_time() \
                                                for tt in self.testcases_tools}
        checkpoint_handler.set_finished(detailed_exectime_obj=detailed_exectime)
    #~ def generate_tests()
    
    def get_meta_column(column, toolname):
        return ":".join([toolname, column])
    #~ def get_meta_column()

    def reverse_meta_testcase(meta_testcase, toolname):
        parts = meta_testcase.split(':', 1)
        assert len(parts) >= 2, "invalibd meta testcase"
        toolname, testcase = parts
        return toolname, testcase
    #~ def reverse_meta_testcase()

    def get_testcase_info_object(self):
        return common_fs.loadJSON(self.get_testcase_info_file())
    #~ def get_testcase_info_object()

    def storeTestcaseInfoToFile(self, data_object):
        common_fs.dumpJSON(data_object, self.get_testcase_info_file())
    #~ def storeTestcaseInfoToFile()

    def get_testcase_info_file(self):
        return self.testcases_info_file
    #~ def get_testcase_info_file()

    def get_test_tool_out_folder(test_toolname, top_outdir=None):
        if top_outdir is None:
            top_outdir = self.tests_working_dir
        return os.path.join(top_outdir, test_toolname)
    #~ def get_test_tool_out_folder()

    def get_test_tool_checkpoint_files(self, test_toolname, top_checkpoint_dir=None):
        if top_checkpoint_dir is None:
            top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                            test_toolname+"_checkpoint.state"+suffix) \
                            for suffix in ("", ".backup")]
    #~ def get_test_tool_checkpoint_files()
        
    def get_checkpoint_files(self):
        top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                        "checkpoint.state"+suffix) \
                        for suffix in ("", ".backup")]
    #~ def get_checkpoint_files()

    def get_checkpoint_state_object(self):
        return self.checkpointer
    #~ def get_checkpoint_state_object()

    def has_checkpointer(self):
        return self.checkpointer is not None
#~ class MetaTestcaseTool
