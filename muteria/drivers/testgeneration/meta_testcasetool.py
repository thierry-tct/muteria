#
# [LICENCE]
#
"""
This module is used through MetaTestcaseTool class
Which access the relevant testcase tools as specified

The tools are organized by programming language
For each language, there is a folder for each tool, 
named after the tool in lowercase

Each testcase tool package have the following in the __init__.py file:
>>> import <Module>.<class extending BaseTestcaseTool> as TestcaseTool
"""

from __future__ import print_function
import os
import sys
import glob
import shutil
import copy
import logging
import multiprocessing
import joblib

import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from muteria.drivers import ToolsModulesLoader
from muteria.drivers import DriversUtils

from muteria.drivers.checkpoint_handler import CheckPointHandler

from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject
from muteria.drivers.testgeneration import TestToolType

from muteria.drivers.testgeneration.custom_dev_testcase.custom_dev_testcase \
                                                        import CustomTestcases

ERROR_HANDLER = common_mix.ErrorHandler

class MetaTestcaseTool(object):
    ''' 
    '''

    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"
    TOOL_TYPE_KEY = "tool_type"

    # The Fault execution matrix has a unique key represented by this string
    FAULT_MATRIX_KEY = "fault_revealed"
    PROGRAM_EXECOUTPUT_KEY = "program"

    @classmethod
    def get_toolnames_by_types_by_language(cls):
        """ get imformation about the plugged-in testcase tool drivers.
            :return: a dict having the form:
                    {
                        language: {
                            TestToolType: [
                                (toolname, is_installed?)
                            ]
                        }
                    }
        """
        modules_dict = ToolsModulesLoader.get_tools_modules( \
                                            ToolsModulesLoader.TESTCASES_TOOLS)
        res = {}
        for language in modules_dict:
            res[language] = {}
            for toolname in modules_dict[language]:
                for tooltype in TestToolType:
                    tooltype_name = tooltype.get_field_value()
                    try:
                        # the tooltype is returned by config.get_tool_type()
                        TestcaseTool = getattr(\
                                            modules_dict[language][toolname],\
                                                                tooltype_name)
                        if TestcaseTool is not None:
                            if tooltype_name not in res[language]:
                                res[language][tooltype_name] = []
                            res[language][tooltype_name].append(\
                                        (toolname, TestcaseTool.installed()))
                    except AttributeError:
                        ERROR_HANDLER.error_exit("{} {} {} {}".format( \
                                "(REPORT BUG) The test case tool of type", \
                                tooltype_name,\
                                "is not present for test tool", toolname), \
                                                                    __file__)
        
        # Add custom dev test
        for language in res:
            tooltype = TestToolType.USE_ONLY_CODE
            res[language][tooltype.get_tool_type_classname()] = \
                                    (CustomTestcases.CUSTOM_TEST_TOOLNAME, \
                                                CustomTestcases.installed())
        return res
    #~ def get_toolnames_by_types_by_language()

    def __init__(self, language, tests_working_dir, code_builds_factory,
                                test_tool_config_list, head_explorer):

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
        self.language = language.lower()
        self.tests_working_dir = tests_working_dir
        self.code_builds_factory = code_builds_factory
        self.test_tool_config_list = test_tool_config_list
        self.head_explorer = head_explorer

        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.tests_working_dir is not None, \
                                    "Must specify tests_working_dir", __file__)
        ERROR_HANDLER.assert_true(len(self.test_tool_config_list) == \
                                len(set([c.get_tool_config_alias() for c in \
                                            self.test_tool_config_list])), \
                        "some tool configs appear multiple times", __file__)

        # Set Indirect Arguments Variables
        self.checkpoints_dir = os.path.join(self.tests_working_dir, \
                                                            "_checkpoints_")
        self.testcases_info_file = \
                os.path.join(self.tests_working_dir, "testcasesInfos.json")
        self.flakiness_workdir = \
                            os.path.join(self.tests_working_dir, "Flakiness")

        # Verify Indirect Arguments Variables

        # Initialize other Fields
        self.testcases_configured_tools = {}
        self.checkpointer = None 

        # Make Initialization Computation ()
        ## Create dirs
        if not os.path.isdir(self.tests_working_dir):
            self.clear_working_dir()

        ## Set the checkpointer
        self.checkpointer = common_fs.CheckpointState(\
                                                *self._get_checkpoint_files())
        
        self.custom_devtest_toolalias = None

        # Create the diffent tools
        for idx in range(len(test_tool_config_list)):
            config = test_tool_config_list[idx]
            toolname = config.get_tool_name()
            toolalias = config.get_tool_config_alias()
            tool_working_dir = self._get_test_tool_out_folder(toolalias)
            tool_checkpointer = common_fs.CheckpointState(\
                            *self._get_test_tool_checkpoint_files(toolalias))
            self.checkpointer.add_dep_checkpoint_state(tool_checkpointer)
            self.testcases_configured_tools[toolalias] = {
                self.TOOL_OBJ_KEY: self._create_testcase_tool(toolname, \
                                                    tool_working_dir, config, \
                                                    tool_checkpointer),
                self.TOOL_WORKDIR_KEY: tool_working_dir,
                self.TOOL_TYPE_KEY: config.get_tool_type()
            }
    #~ def __init__()

    def _create_testcase_tool(self, toolname, tool_working_dir, \
                                                    config, tool_checkpointer):
        '''
            
        '''
        # Check for custom testcase
        if toolname == CustomTestcases.CUSTOM_TEST_TOOLNAME:
            TestcaseTool = CustomTestcases
            ERROR_HANDLER.assert_true(self.custom_devtest_toolalias is None, \
                        "Must specify custom dev tests only once", __file__)
            self.custom_devtest_toolalias = config.get_tool_config_alias()
        else:
            ERROR_HANDLER.assert_true( \
                toolname in self.modules_dict[self.language],
                "Invalid toolname given: {}".format(toolname), __file__)
            try:
                # the tooltype is returned by config.get_tool_type()
                TestcaseTool = getattr(\
                                self.modules_dict[self.language][toolname],\
                                config.get_tool_type().get_field_value())
            except AttributeError:
                ERROR_HANDLER.error_exit("{} {} {} {}".format( \
                                    "(REPORT BUG) The test case tool of type",\
                                    config.get_tool_type().get_field_value(),\
                                    "is not present for test tool", toolname),\
                                                                    __file__)

            ERROR_HANDLER.assert_true(TestcaseTool is not None, \
                                    "The {} language's tool {} {} {}.".format(\
                                    self.language, toolname, \
                                    "does not implement the test tool type", \
                                        config.get_tool_type().get_str()), \
                                                                    __file__)

        testcase_tool = TestcaseTool(tool_working_dir, \
                                        self.code_builds_factory, config, \
                                                    self.head_explorer, \
                                                    tool_checkpointer, \
                                                    parent_meta_tool=self)
        return testcase_tool
    #~ def _create_testcase_tool()

    def check_tools_installed(self):
        non_installed = []
        for toolalias, tool_obj in self.testcases_configured_tools.items():
            if not tool_obj[self.TOOL_OBJ_KEY].tool_installed():
                non_installed.append(toolalias)
        if len(non_installed) > 0:
            ERROR_HANDLER.error_exit("{}: {}".format(\
                            "The following Testcase tools are not installed", \
                            str(non_installed)))
    #~ def check_tools_installed()

    def get_devtest_toolalias(self):
        return self.custom_devtest_toolalias
    #~ def get_devtest_toolalias()


    def clear_working_dir(self):
        if os.path.isdir(self.tests_working_dir):
            shutil.rmtree(self.tests_working_dir)
        os.mkdir(self.tests_working_dir)
        if os.path.isdir(self.checkpoints_dir):
            shutil.rmtree(self.checkpoints_dir)
        os.mkdir(self.checkpoints_dir)
        for _, tool_dat in list(self.testcases_configured_tools.items()):
            tool_dat[self.TOOL_OBJ_KEY].clear_working_dir()
    #~ def clear_working_dir()    


    def _get_default_exe_path_map(self):
        exes, _ = self.code_builds_factory.repository_manager\
                                                .get_relative_exe_path_map()
        return {v:None for v in exes}
    #~ def _get_default_exe_path_map()

    def execute_testcase (self, meta_testcase, exe_path_map, env_vars, \
                                        timeout=None, \
                                        use_recorded_timeout_times=None, \
                                        recalculate_execution_times=False, \
                                        with_output_summary=True, \
                                        hash_outlog=True):
        '''
        Execute a test case with the given executable and 
        say whether it failed

        :param meta_testcase: string name of the test cases to execute
        :param exe_path_map: string representing the file system path to 
                        the executable to execute with the test
        :param env_vars: dict of environment variables to set before
                        executing the test ({<variable>: <value>})
        :returns: pair of:
                - boolean failed verdict of the test 
                        (True if failed, False otherwise)
                - test execution output log hash data object or None
        '''
        
        if exe_path_map is None:
            exe_path_map = self._get_default_exe_path_map()

        # Find which test tool's the testcase is, then execute
        ttoolalias, testcase = DriversUtils.reverse_meta_element(meta_testcase)
        ERROR_HANDLER.assert_true( \
                            ttoolalias in self.testcases_configured_tools, \
                            "Test tool {} not registered".format(ttoolalias), \
                                                                    __file__)
        ttool = self.testcases_configured_tools[ttoolalias][self.TOOL_OBJ_KEY]
        return ttool.execute_testcase(testcase, exe_path_map, env_vars, \
                            timeout=timeout, \
                            use_recorded_timeout_times=\
                                                use_recorded_timeout_times, \
                            recalculate_execution_times=\
                                                recalculate_execution_times, \
                            with_output_summary=with_output_summary, \
                            hash_outlog=hash_outlog)
    #~ def execute_testcase()

    def runtests(self, meta_testcases=None, exe_path_map=None, env_vars=None, \
                        stop_on_failure=False, \
                        per_test_timeout=None, \
                        use_recorded_timeout_times=None, \
                        recalculate_execution_times=False, \
                        fault_test_execution_matrix_file=None, \
                        fault_test_execution_execoutput_file=None, \
                        with_output_summary=True, \
                        hash_outlog=True, \
                        test_prioritization_module=None, \
                        parallel_test_count=1, \
                        parallel_test_scheduler=None, \
                        restart_checkpointer=False,
                        finish_destroy_checkpointer=True):
        '''
        Execute the list of test cases with the given executable and 
        say, for each test case, whether it failed

        :param meta_testcases: list of test cases to execute
        :param exe_path_map: string representing the file system path to 
                        the executable to execute with the tests
        :param env_vars: dict of environment variables to set before
                        executing each test ({<variable>: <value>})
        :param stop_on_failure: decide whether to stop the test 
                        execution once a test fails
        :param fault_test_execution_matrix_file: Optional matrix file 
                        to store the tests' pass fail execution data
        :param fault_test_execution_execoutput_file: Optional output log file 
                        to store the tests' execution actual output (hashed)
        :param with_output_summary: decide whether to return outlog hash 
        :param test_prioritization_module: Specify the test prioritization
                        module. 
                        (TODO: Implement support)
        :param parallel_test_count: Specify the number of parallel test
                        Execution. must be an integer >= 1 or None.
                        When None, the max possible value is used.
        :param parallel_test_scheduler: Specify the function that will
                        handle parallel test scheduling by tool, using
                        the test execution optimizer. 
                        (TODO: Implement support)

        :type restart_checkointer: bool
        :param restart_checkointer: Decide whether to discard checkpoint
                        and restart anew.

        :type finish_destroy_checkpointer: bool
        :param finish_destroy_checkpointer: Decide whether to automatically 
                        destroy the checkpointer when done or not
                        Useful is caller has a checkpointer to update. 

        :returns: dict of testcase and their failed verdict.
                 {<test case name>: <True if failed, False if passed,
                    UNCERTAIN_TEST_VERDICT if uncertain>}
                 If stop_on_failure is True, only return the tests that 
                 have been executed until the failure
        '''
        
        ERROR_HANDLER.assert_true(meta_testcases is not None, \
                                            "Must specify testcases", __file__)

        # FIXME: Make sure that the support are implemented for 
        # parallelism and test prioritization. Remove the code bellow 
        # once supported:
        ERROR_HANDLER.assert_true(test_prioritization_module is None, \
                        "Must implement test prioritization support here", \
                                                                    __file__)
        ERROR_HANDLER.assert_true(parallel_test_scheduler is None, \
                    "Must implement parallel tests execution support here", \
                                                                    __file__)
        #~FIXMEnd

        # Check arguments Validity
        if exe_path_map is None:
            exe_path_map = self._get_default_exe_path_map()

        ERROR_HANDLER.assert_true(parallel_test_count is None \
                                        or parallel_test_count >= 1, \
                                "invalid parallel tests count ({})".format(\
                                                parallel_test_count), __file__)

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "runtests"
        cp_task_id = 1
        checkpoint_handler = \
                CheckPointHandler(self.get_checkpoint_state_object())
        if restart_checkpointer:
            checkpoint_handler.restart()
        if checkpoint_handler.is_finished():
            logging.warning("%s %s" %("The function 'runtests' is finished", \
                "according to checkpoint, but called again. None returned"))
            if common_mix.confirm_execution("%s %s" % ( \
                                        "Function 'runtests' is already", \
                                        "finished, do you want to restart?")):
                checkpoint_handler.restart()
                logging.info("Restarting the finished 'runtests'")
            else:
                ERROR_HANDLER.error_exit(err_string="%s %s %s" % (\
                        "Execution halted. Cannot continue because no value", \
                        " can be returned. Check the results of the", \
                        "finished execution"), call_location=__file__)

        # @Checkpoint: Get the saved payload (data kapt for each tool)
        # pair list of testfailed verdict and execution output
        meta_test_failedverdicts_outlog = \
                                    checkpoint_handler.get_optional_payload()
        if meta_test_failedverdicts_outlog is None:
            meta_test_failedverdicts_outlog = [{}, {}]

        # Make sure the tests are unique
        ERROR_HANDLER.assert_true(len(meta_testcases) == \
                                                len(set(meta_testcases)), \
                                        "not all tests are unique", __file__)

        testcases_by_tool = {}
        for meta_testcase in meta_testcases:
            ttoolalias, testcase = \
                            DriversUtils.reverse_meta_element(meta_testcase)
            if ttoolalias not in testcases_by_tool:
                testcases_by_tool[ttoolalias] = []
            testcases_by_tool[ttoolalias].append(testcase)
            
        candidate_aliases = []
        for tpos, ttoolalias in enumerate(testcases_by_tool.keys()):
            # @Checkpoint: Check whether already executed
            if not checkpoint_handler.is_to_execute(func_name=cp_func_name, \
                                                taskid=cp_task_id, \
                                                tool=ttoolalias):
                continue
            candidate_aliases.append(ttoolalias)

        shared_loc = multiprocessing.RLock()

        next_parallel_count = parallel_test_count

        def tool_parallel_test_exec(ttoolalias):
            # Actual execution
            found_a_failure=False
            ttool = \
                self.testcases_configured_tools[ttoolalias][self.TOOL_OBJ_KEY]
            test_failed_verdicts, test_execoutput = ttool.runtests( \
                                            testcases_by_tool[ttoolalias], \
                                            exe_path_map, env_vars, \
                                            stop_on_failure, \
                                            per_test_timeout=per_test_timeout,
                                            use_recorded_timeout_times=\
                                                use_recorded_timeout_times, \
                                            recalculate_execution_times=\
                                                recalculate_execution_times, \
                                            with_output_summary=\
                                                        with_output_summary, \
                                            hash_outlog=hash_outlog, \
                                            parallel_count=next_parallel_count)
            with shared_loc:
                for testcase in test_failed_verdicts:
                    meta_testcase =  DriversUtils.make_meta_element(\
                                                        testcase, ttoolalias)
                    meta_test_failedverdicts_outlog[0][meta_testcase] = \
                                                test_failed_verdicts[testcase]
                    meta_test_failedverdicts_outlog[1][meta_testcase] = \
                                                    test_execoutput[testcase]
                    if not found_a_failure \
                                and test_failed_verdicts[testcase] == \
                                common_mix.GlobalConstants.COMMAND_UNCERTAIN:
                        found_a_failure = True

                # @Checkpoint: Chekpointing
                checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                taskid=cp_task_id, \
                                tool=ttoolalias, \
                                opt_payload=meta_test_failedverdicts_outlog)
            return found_a_failure
        #~ def tool_parallel_test_exec()

        # minimum number of tests for parallelism
        ptest_tresh = 5

        if len(candidate_aliases) > 1 and len(meta_testcases) >= ptest_tresh \
                and (parallel_test_count is None or parallel_test_count > 1):
            if parallel_test_count is None:
                paralle_count = min(len(candidate_aliases), \
                                                multiprocessing.cpu_count())
            else:
                paralle_count = min(len(candidate_aliases), \
                                                        parallel_test_count)
                #next_parallel_count = 1
            joblib.Parallel(n_jobs=paralle_count, require='sharedmem')\
                    (joblib.delayed(tool_parallel_test_exec)(ttoolalias) \
                        for ttoolalias in candidate_aliases)
        else:
            for tpos, ttoolalias in enumerate(candidate_aliases):
                found_a_failure = tool_parallel_test_exec(ttoolalias)
                if stop_on_failure and found_a_failure:
                    # @Checkpoint: Chekpointing for remaining tools
                    for rem_tool in list(testcases_by_tool.keys())[tpos+1:]:
                        checkpoint_handler.do_checkpoint(\
                                func_name=cp_func_name, \
                                taskid=cp_task_id, \
                                tool=rem_tool, \
                                opt_payload=meta_test_failedverdicts_outlog)
                    break
                                        
        if stop_on_failure:
            # Make sure the non executed test has the uncertain value (None)
            if len(meta_test_failedverdicts_outlog[0]) < len(meta_testcases):
                for meta_testcase in set(meta_testcases) - \
                                    set(meta_test_failedverdicts_outlog[0]):
                    meta_test_failedverdicts_outlog[0][meta_testcase] = \
                            common_mix.GlobalConstants.UNCERTAIN_TEST_VERDICT
                    meta_test_failedverdicts_outlog[1][meta_testcase] = \
                            common_matrices.OutputLogData.\
                                                    UNCERTAIN_TEST_OUTLOGDATA
                    
        ERROR_HANDLER.assert_true(len(meta_test_failedverdicts_outlog[0]) == \
                                                        len(meta_testcases), \
                            "Not all tests have a verdict reported", __file__)

        if fault_test_execution_matrix_file is not None:
            # Load or Create the matrix 
            fault_test_execution_matrix = common_matrices.ExecutionMatrix( \
                                filename=fault_test_execution_matrix_file, \
                                            non_key_col_list=meta_testcases)
            ERROR_HANDLER.assert_true(fault_test_execution_matrix.is_empty(), \
                                "matrix must be empty. Filename is:"
                                " "+fault_test_execution_matrix_file, __file__)
            failverdict2val = {
                common_mix.GlobalConstants.FAIL_TEST_VERDICT: \
                        fault_test_execution_matrix.getActiveCellDefaultVal(),
                common_mix.GlobalConstants.PASS_TEST_VERDICT: \
                            fault_test_execution_matrix.getInactiveCellVal(),
                common_mix.GlobalConstants.UNCERTAIN_TEST_VERDICT: \
                    fault_test_execution_matrix.getUncertainCellDefaultVal(),
            }
            cells_dict = {}
            for meta_testcase in meta_test_failedverdicts_outlog[0]:
                cells_dict[meta_testcase] = failverdict2val[\
                            meta_test_failedverdicts_outlog[0][meta_testcase]]

            fault_test_execution_matrix.add_row_by_key(self.FAULT_MATRIX_KEY, \
                                                cells_dict, serialize=True)

        if fault_test_execution_execoutput_file is not None:
            # Load or Create the data object 
            fault_test_execution_execoutput = common_matrices.OutputLogData( \
                                filename=fault_test_execution_execoutput_file)
            ERROR_HANDLER.assert_true(\
                            fault_test_execution_execoutput.is_empty(), \
                                        "outlog data must be empty", __file__)
            fault_test_execution_execoutput.add_data(\
                                    {self.PROGRAM_EXECOUTPUT_KEY: \
                                         meta_test_failedverdicts_outlog[1]}, \
                                                                serialize=True)


        # @Checkpoint: Finished
        detailed_exectime = {}
        for ttoolalias in testcases_by_tool.keys():
            tt = self.testcases_configured_tools[ttoolalias][self.TOOL_OBJ_KEY]
            detailed_exectime[ttoolalias] = (\
                        tt.get_checkpointer().get_execution_time(),\
                        tt.get_checkpointer().get_detailed_execution_time())

        checkpoint_handler.set_finished( \
                                    detailed_exectime_obj=detailed_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()

        return meta_test_failedverdicts_outlog
    #~ def runtests()

    def get_candidate_tools_aliases(self, test_tool_type_list):
        candidate_tools_aliases = []
        for test_tool_type in test_tool_type_list:
            # validate the test_tool_types values
            ERROR_HANDLER.assert_true(\
                                TestToolType.is_valid(test_tool_type), \
                    "Invalid test tool type passed to test generation", \
                                                                __file__)
            for ttoolalias in self.testcases_configured_tools:
                if self.testcases_configured_tools[ttoolalias]\
                                    [self.TOOL_TYPE_KEY] == test_tool_type:
                    candidate_tools_aliases.append(ttoolalias) 
        return candidate_tools_aliases
    #~ def get_candidate_tools_aliases()

    def generate_tests (self, meta_criteria_tool_obj=None, \
                                exe_path_map=None, \
                                test_tool_type_list=None, \
                                max_time=None, \
                                test_generation_guidance_obj=None, \
                                parallel_testgen_count=1, \
                                restart_checkpointer=False, \
                                finish_destroy_checkpointer=True):
        """ This method should be used to generate the tests and must 
            always have a single instance running (it has single checkpoint
            file). 
            Note: The caller must explicitely destroy the checkpointer
            after this call succeed, to ensure that a sceduler will not
            re-execute this 
        :type meta_criteria_tool_obj:
        :param meta_criteria_tool_obj:

        :type exe_path_map:
        :param exe_path_map:

        :type test_tool_type_list:
        :param test_tool_type_list:
    
        :type \test_generation_guidance_obj:
        :param \test_generation_guidance_obj:
    
        :type \parallel_testgen_count:
        :param \parallel_testgen_count:

        :type restart_checkointer: bool
        :param restart_checkointer: Decide whether to discard checkpoint
                        and restart anew.

        :type finish_destroy_checkpointer: bool
        :param finish_destroy_checkpointer: Decide whether to automatically 
                        destroy the checkpointer when done or not
                        Useful is caller has a checkpointer to update. 
    
        :raises:
    
        :rtype:
        """
        # FIXME: Support test_generation_guidance_obj, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(test_generation_guidance_obj is None, \
                "FIXME: Must first implement support for test gen guidance")
        ERROR_HANDLER.assert_true(parallel_testgen_count <= 1, \
                "FIXME: Must first implement support for parallel test gen")
        #~ FXIMEnd

        # Check arguments Validity
        if exe_path_map is None:
            exe_path_map = self._get_default_exe_path_map()

        ERROR_HANDLER.assert_true(parallel_testgen_count > 0, \
                    "invalid parallel test generation count: {}. {}".format( \
                                    parallel_testgen_count, "must be >= 1"))
        if test_tool_type_list is None:
            candidate_tools_aliases = self.testcases_configured_tools.keys()
        else:
            ERROR_HANDLER.assert_true(len(test_tool_type_list) > 0,\
                                "Invalid test_tool_type_list passed (empty)", \
                                                                    __file__)
            candidate_tools_aliases = self.get_candidate_tools_aliases(\
                                                        test_tool_type_list)

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "generate_tests"
        if test_tool_type_list is not None:
            for test_tool_type in sorted(test_tool_type_list):
                cp_func_name += ":" + test_tool_type.get_str()
        cp_task_id = 1
        checkpoint_handler = CheckPointHandler(\
                                            self.get_checkpoint_state_object())
        if restart_checkpointer:
            checkpoint_handler.restart()
        if checkpoint_handler.is_finished():
            return

        # Generate
        for ttoolalias in candidate_tools_aliases:
            ttool = self.testcases_configured_tools[ttoolalias]\
                                                            [self.TOOL_OBJ_KEY]
            # Make sure to execute the right one
            if meta_criteria_tool_obj is None:
                if ttool.requires_criteria_instrumented():
                    continue
            else:
                if not ttool.requires_criteria_instrumented():
                    continue

            # Check whether already executed
            if checkpoint_handler.is_to_execute(func_name=cp_func_name, \
                                                taskid=cp_task_id, \
                                                tool=ttoolalias):

                # Actual Execution
                ttool.generate_tests(exe_path_map, \
                            meta_criteria_tool_obj=meta_criteria_tool_obj, \
                            max_time=max_time)

                # @Checkpoint: Checkpointing
                checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                                taskid=cp_task_id, \
                                                tool=ttoolalias)

        # Invalidate any existing testcase info so it can be recomputed
        self._invalidate_testcase_info()

        # @Checkpoint: Finished
        detailed_exectime = {}
        for ttoolalias in candidate_tools_aliases:
            tt = self.testcases_configured_tools[ttoolalias][self.TOOL_OBJ_KEY]
            detailed_exectime[ttoolalias] = (\
                        tt.get_checkpointer().get_execution_time(),\
                        tt.get_checkpointer().get_detailed_execution_time())

        checkpoint_handler.set_finished( \
                                    detailed_exectime_obj=detailed_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()
    #~ def generate_tests()
    
    def _compute_testcases_info(self, candidate_tool_aliases=None):
        meta_testcase_info_obj = TestcasesInfoObject()
        if candidate_tool_aliases is None:
            candidate_tool_aliases = self.testcases_configured_tools.keys()
        for ttoolalias in candidate_tool_aliases:
            ttool = \
                self.testcases_configured_tools[ttoolalias][self.TOOL_OBJ_KEY]
            tool_testcase_info = ttool.get_testcase_info_object()
            old2new_tests = {}
            for t_test in tool_testcase_info.get_tests_list():
                meta_t_key = DriversUtils.make_meta_element(t_test, ttoolalias)
                old2new_tests[t_test] = meta_t_key
            meta_testcase_info_obj.update_using(ttoolalias, old2new_tests, \
                                                            tool_testcase_info)
        return meta_testcase_info_obj
    #~ def _compute_testcases_info()
    
    def get_testcase_info_object(self, candidate_tool_aliases=None):
        tc_info = TestcasesInfoObject()
        tc_info.load_from_file(self.get_testcase_info_file(\
                                                       candidate_tool_aliases))
        return tc_info
    #~ def get_testcase_info_object()

    def get_testcase_info_file(self, candidate_tool_aliases=None):
        # Compute and write the testcase info if not present
        # only place where the meta info is written

        ## commented because many stages for test generation
        #if self._testcase_info_is_invalidated(): 
        self._compute_testcases_info(candidate_tool_aliases).write_to_file(\
                                    self._unchecked_get_testcase_info_file())
        return self._unchecked_get_testcase_info_file()
    #~ def get_testcase_info_file()

    def _unchecked_get_testcase_info_file(self):
        return self.testcases_info_file
    #~ def _unchecked_get_testcase_info_file():

    def _invalidate_testcase_info(self):
        if os.path.isfile(self._unchecked_get_testcase_info_file()):
            os.remove(self._unchecked_get_testcase_info_file())
    #~ def _invalidate_testcase_info()

    def _testcase_info_is_invalidated(self):
        return not os.path.isfile(self._unchecked_get_testcase_info_file())
    #~ def _testcase_info_is_invalidated()

    def _get_test_tool_out_folder(self, test_toolname, top_outdir=None):
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

    def get_test_tools_by_name(self, toolname):
        res = {}
        for alias, data in self.testcases_configured_tools.items():
            if data[self.TOOL_OBJ_KEY].get_toolname() == toolname:
                res[alias] = data[self.TOOL_OBJ_KEY]
        return res
    #~ def get_test_tools_by_name()

    def get_checkpoint_state_object(self):
        return self.checkpointer
    #~ def get_checkpoint_state_object()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer()

    ######################################
    ############ OTHER FUNCTION ##########
    ######################################
    def get_flakiness_workdir(self):
        return self.flakiness_workdir
    #~ def get_flakiness_workdir()

    def check_get_flakiness(self, meta_testcases, repeat_count=2):
        """
            Check if tests have flakiness by running multiple times
            :return: The list of flaky tests
        """
        ERROR_HANDLER.assert_true(repeat_count > 1, "Cannot check flakiness"
                                    " with less than on repetition", __file__)

        if os.path.isdir(self.flakiness_workdir):
            shutil.rmtree(self.flakiness_workdir)
        os.mkdir(self.flakiness_workdir)

        outlog_files = [os.path.join(self.flakiness_workdir, \
                            str(of)+'-out.json') for of in range(repeat_count)]
        matrix_files = [os.path.join(self.flakiness_workdir, \
                            str(of)+'-mat.csv') for of in range(repeat_count)]
        
        def run(rep, test_list, hash_outlog):
            self.runtests(test_list, \
                        fault_test_execution_matrix_file=matrix_files[rep], \
                        fault_test_execution_execoutput_file=\
                                                            outlog_files[rep],\
                        with_output_summary=True, \
                        hash_outlog=hash_outlog)
        #~ def run()

        # Execute with repetition and get output summaries
        for rep in range(repeat_count):
            run(rep, meta_testcases, True)

        # get flaky tests list
        flaky_tests = set()
        fix_outdata = common_matrices.OutputLogData(filename=outlog_files[0])
        fix_outdata = list(fix_outdata.get_zip_objective_and_data())[0][1]
        for i in range(1, repeat_count):
            other_outdata = common_matrices.OutputLogData(\
                                                    filename=outlog_files[i])
            other_outdata = list(\
                            other_outdata.get_zip_objective_and_data())[0][1]
            for test, t_dat_fix in fix_outdata.items():
                if test in flaky_tests:
                    continue
                t_dat_other = other_outdata[test]
                if not common_matrices.OutputLogData.outlogdata_equiv(\
                                                    t_dat_fix, t_dat_other):
                    flaky_tests.add(test)

        ## cleanup
        for f in outlog_files + matrix_files:
            if os.path.isfile(f):
                os.remove(f)

        # get flaky tests outputs
        if len(flaky_tests) > 0:
            for rep in range(repeat_count):
                run(rep, list(flaky_tests), False)
            flaky_test_list_file = os.path.join(self.flakiness_workdir, \
                                                        "flaky_test_list.json")
            logging.warning("There were some flaky tests (see file {})"\
                                                .format(flaky_test_list_file))
            common_fs.dumpJSON(list(flaky_tests), flaky_test_list_file, \
                                                                pretty=True)
        return list(flaky_tests)
    #~ def check_get_flakiness()
#~ class MetaTestcaseTool
