#
# [LICENCE]
#
""" Code coverage tool module. The class of interest is BaseCOdecoverageTool.

The tools are organized by programming language

For each language, there is a folder for each tool, 
named after the tool in all lowercase , starting with letter or underscore(_),
The remaining caracters are either letter, number or underscore

XXX Each criteria tool package must have the 
following in the __init__.py file:
>>> import <Module>.<class extending BaseCodecoverageTool> as CodecoverageTool
"""

from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import abc
import tqdm

import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from muteria.drivers.checkpoint_handler import CheckPointHandler
from muteria.drivers.criteria import TestCriteria
from muteria.drivers import DriversUtils

ERROR_HANDLER = common_mix.ErrorHandler

class BaseCriteriaTool(abc.ABC):
    '''
    '''
    @classmethod
    def get_supported_criteria(cls):
        return cls._get_meta_instrumentation_criteria() + \
                                cls._get_separated_instrumentation_criteria()
    #~ def get_supported_criteria()

    def __init__(self, meta_test_generation_obj, criteria_working_dir, 
                                code_builds_factory, config, checkpointer):
        # Set Constants
        
        # Set Direct Arguments Variables
        self.meta_test_generation_obj = meta_test_generation_obj
        self.criteria_working_dir = criteria_working_dir
        self.code_builds_factory = code_builds_factory
        self.config = config
        self.checkpointer = checkpointer
        
        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.criteria_working_dir is not None, \
                            "Must specify criteria_working_dir", __file__)
        
        # Set Indirect Arguments Variables
        ## put the instrumented code into this folder (to be created by user)
        self.instrumented_code_storage_dir = os.path.join(
                        self.criteria_working_dir, "instrumented_code")
        self.custom_binary_dir = None
        if self.config.tool_user_custom is not None:
            self.custom_binary_dir = \
                        self.config.tool_user_custom.PATH_TO_TOOL_BINARY_DIR

        
        # Verify indirect Arguments Variables
        
        # Initialize Other Fields
        
        # Make Initialization Computation
        ## Create dirs
        if not os.path.isdir(self.criteria_working_dir):
            self.clear_working_dir()
    #~ def __init__()

    def clear_working_dir(self):
        if os.path.isdir(self.criteria_working_dir):
            try:
                shutil.rmtree(self.criteria_working_dir)
            except PermissionError:
                self._dir_chmod777(self.criteria_working_dir)
                shutil.rmtree(self.criteria_working_dir)
        os.mkdir(self.criteria_working_dir)
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
    #~ def has_checkpointer()

    def _runtest_meta_criterion_program (self, testcases, criterion_to_matrix,\
                                    criterion_to_executionoutput, \
                                    criteria_element_list_by_criteria, \
                                    cover_criteria_elements_once=False, \
                                    prioritization_module_by_criteria=None, \
                                    test_parallel_count=1):
        """
        """

        logging.debug("# Executing meta {}: {} ...".format("criteria" if \
                                len(criterion_to_matrix) > 1 else "criterion",\
                                [c.get_str() for c in criterion_to_matrix]))

        # get instrumented executables
        criterion2executable_path = \
                                self.get_instrumented_executable_paths_map( \
                                                    criterion_to_matrix.keys())

        # get environment vars
        result_dir_tmp = os.path.join(self.criteria_working_dir, \
                                                "criteria_meta_result_tmp")
        if os.path.isdir(result_dir_tmp):
            try:
                shutil.rmtree(result_dir_tmp)
            except PermissionError:
                self._dir_chmod777(result_dir_tmp)
                shutil.rmtree(result_dir_tmp)

        criterion2environment_vars = self._get_criteria_environment_vars( \
                                                            result_dir_tmp, \
                                enabled_criteria=criterion_to_matrix.keys())

        ERROR_HANDLER.assert_true(set(criterion2executable_path) == \
                                            set(criterion2environment_vars), \
                        "mismatch between exe_path_map and env_vars", __file__)

        criterialist = criterion2executable_path.keys()

        # group criteria
        groups = self._get_criteria_groups(criterion2executable_path,\
                                                    criterion2environment_vars)

        # important tmp vars
        criterion2coverage_per_test = \
                                {criterion: {} for criterion in criterialist}
        criterion2metaoutlog_per_test = {}
        a_criterion_has_outlog = False
        for criterion in criterialist:
            if criterion_to_executionoutput is None:
                criterion2metaoutlog_per_test[criterion] = None
            else:
                criterion2metaoutlog_per_test[criterion] = {}
                a_criterion_has_outlog = True

        timeout_times = self.config.META_TEST_EXECUTION_EXTRA_TIMEOUT_TIMES

        # Execute each test and gather the data
        processbar = tqdm.tqdm(testcases, leave=False, dynamic_ncols=True) 
        for testcase in processbar: 
            processbar.set_description("Running Test %s"% testcase)
            for cg_criteria, cg_exe_path_map, cg_env_vars in groups:
                # Create reult_tmp_dir
                os.mkdir(result_dir_tmp, mode=0o777)

                # run testcase
                test_verdict = self.meta_test_generation_obj.execute_testcase(\
                                            testcase, \
                                            exe_path_map=cg_exe_path_map, \
                                            env_vars=cg_env_vars,\
                                            use_recorded_timeout_times=\
                                                                timeout_times)
                
                # Collect temporary data into result_dir_tmp
                self._collect_temporary_coverage_data(\
                                                cg_criteria, test_verdict, \
                                                cg_env_vars, result_dir_tmp, \
                                                testcase)

                # extract coverage
                coverage_tmp_data_per_criterion = \
                                self._extract_coverage_data_of_a_test(\
                                                cg_criteria, test_verdict, \
                                                    result_dir_tmp)
                if a_criterion_has_outlog:
                    metaoutlog_tmp_data_per_criterion = \
                                    self._extract_metaoutlog_data_of_a_test( \
                                                cg_criteria, test_verdict, \
                                                    result_dir_tmp)
                # update data
                for criterion in cg_criteria:
                    if len(criterion2coverage_per_test[criterion]) == 0:
                        for elem in coverage_tmp_data_per_criterion[criterion]:
                            criterion2coverage_per_test[criterion][elem] = {}
                        if criterion_to_executionoutput[criterion] is not None:
                            for elem in metaoutlog_tmp_data_per_criterion[\
                                                                    criterion]:
                                criterion2metaoutlog_per_test[criterion]\
                                                                    [elem] = {}

                    for elem in coverage_tmp_data_per_criterion[criterion]:
                        # verify that the value is positive or null
                        v_elem = coverage_tmp_data_per_criterion[criterion]\
                                                                        [elem]
                        ERROR_HANDLER.assert_true(type(v_elem) == int, \
                                        "cov num type must be int", __file__)
                        ERROR_HANDLER.assert_true(v_elem >= 0, \
                                        "invalid cov num(negative)", __file__)
                        try:
                            res = criterion2coverage_per_test[criterion][elem]
                        except KeyError:
                            res = {}
                            criterion2coverage_per_test[criterion][elem] = res

                        res[testcase] = coverage_tmp_data_per_criterion\
                                                            [criterion][elem]

                    if criterion_to_executionoutput[criterion] is not None:
                        for elem in metaoutlog_tmp_data_per_criterion[\
                                                                    criterion]:
                            try:
                                res = criterion2metaoutlog_per_test[criterion]\
                                                                        [elem]
                            except KeyError:
                                res = {}
                                criterion2metaoutlog_per_test[criterion][\
                                                                    elem] = res

                            res[testcase] = metaoutlog_tmp_data_per_criterion\
                                                            [criterion][elem]
                            

                # remove dir created for temporal storage
                try:
                    shutil.rmtree(result_dir_tmp)
                except PermissionError:
                    self._dir_chmod777(result_dir_tmp)
                    shutil.rmtree(result_dir_tmp)

        # Write the execution data into the matrices
        # Since for ExecutionMatrix, active is not 0 thus this is direct.
        testcases_set = set(testcases)
        for criterion in criterion2coverage_per_test:
            matrix = criterion_to_matrix[criterion]
            matrix_file = matrix.get_store_filename()
            if matrix_file is not None and os.path.isfile(matrix_file):
                os.remove(matrix_file)
                                    
            for key, value in list(\
                            criterion2coverage_per_test[criterion].items()):
                missing_tests = {t:common_mix.GlobalConstants.\
                                        ELEMENT_NOTCOVERED_VERDICT for t in \
                                                    testcases_set - set(value)}
                value.update(missing_tests)
                matrix.add_row_by_key(key, value, serialize=False)
            # Serialize to disk
            matrix.serialize()

            # outLog
            if criterion_to_executionoutput[criterion] is not None:
                outlog_datfile = criterion_to_executionoutput[criterion]\
                                                        .get_store_filename()
                if outlog_datfile is not None and \
                                                os.path.isfile(outlog_datfile):
                    os.remove(outlog_datfile)

                criterion_to_executionoutput[criterion].add_data(\
                                    criterion2metaoutlog_per_test[criterion], \
                                    serialize=True)
    #~ def _runtest_meta_criterion_program()

    def _runtest_separate_criterion_program (self, criterion, testcases, \
                                    matrix, 
                                    executionoutput, \
                                    criteria_element_list, \
                                    cover_criteria_elements_once=False, \
                                    prioritization_module=None, \
                                    test_parallel_count=1,
                                    serialize_period=5,
                                    checkpoint_handler=None, \
                                    cp_calling_func_name=None, \
                                    cp_calling_done_task_id=None, \
                                    cp_calling_tool=None):
        '''
        Note: Here the temporary matrix is used as checkpoint 
                (with frequency the 'serialize_period' parameter). 
            The checkpointer is mainly used for the execution time
            (TODO: support parallelism: per test outdata)
        '''
        # FIXME: Support parallelism, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(test_parallel_count <= 1, \
                    "FIXME: Must first implement support for parallel mutatio")
        #~ FXIMEnd

        # @Checkpoint: validate
        if checkpoint_handler is not None:
            ERROR_HANDLER.assert_true(cp_calling_func_name is not None)
            ERROR_HANDLER.assert_true(cp_calling_done_task_id is not None)
            ERROR_HANDLER.assert_true(cp_calling_tool is not None)
            cp_data = checkpoint_handler.get_optional_payload()
            if cp_data is None:
                cp_data = [{}, {}]
        else:
            cp_data = [{}, {}]

        failverdict_to_val_map = {
                    common_mix.GlobalConstants.FAIL_TEST_VERDICT: \
                                            matrix.getActiveCellDefaultVal(),
                    common_mix.GlobalConstants.PASS_TEST_VERDICT: \
                                            matrix.getInactiveCellVal(), 
                    common_mix.GlobalConstants.UNCERTAIN_TEST_VERDICT: \
                                            matrix.getUncertainCellDefaultVal()
        }

        assert serialize_period >= 1, \
                            "Serialize period must be an integer in [1,inf["

        # matrix based checkpoint
        completed_elems = set(cp_data[0])

        if criteria_element_list is None:
            criteria_element_list = self.get_criterion_info_object(criterion).\
                                                            get_elements_list()

        ERROR_HANDLER.assert_true(prioritization_module is not None, 
                                        "prioritization module must be passed")
            
        timeout_times = \
                    self.config.SEPARATED_TEST_EXECUTION_EXTRA_TIMEOUT_TIMES

        # in case the test list is empty, do nothing
        if len(testcases) > 0:
            # main loop for elements execution
            num_elems = len(criteria_element_list)
            pos = -1 + len(completed_elems)
            ## prepare the optimizer
            prioritization_module.reset(self.config.get_tool_config_alias(), \
                                            criteria_element_list, testcases)
            while prioritization_module.has_next_test_objective():
                #pos += 1 # Done bellow in the case where it was not completed
                element = prioritization_module.get_next_test_objective()

                # @Checkpointing: check if already executed
                if element in completed_elems:
                    continue
                else:
                    pos += 1

                logging.debug("# Executing {} element {} ({}/{}) ...".format( \
                                    criterion.get_str(), \
                                    DriversUtils.make_meta_element(element, \
                                        self.config.get_tool_config_alias()), \
                                    pos, num_elems))

                # execute element with the given testcases
                element_executable_path = \
                                self._get_criterion_element_executable_path(\
                                                            criterion, element)
                execution_environment_vars = \
                                self._get_criterion_element_environment_vars(\
                                                            criterion, element)
                # run optimizer with all tests of targeting the test objective
                may_cov_tests = prioritization_module\
                                        .get_test_execution_optimizer(element)\
                                        .select_tests(100, is_proportion=True)

                cannot_cov_tests = set(testcases) - set(may_cov_tests)
                
                fail_verdicts, exec_outs_by_tests = \
                                    self.meta_test_generation_obj.runtests(\
                                        meta_testcases=may_cov_tests, \
                                        exe_path_map=element_executable_path, \
                                        env_vars=execution_environment_vars, \
                                        stop_on_failure=\
                                                cover_criteria_elements_once, \
                                        use_recorded_timeout_times=\
                                                            timeout_times, \
                                        with_output_summary=(executionoutput \
                                                                is not None), \
                                        parallel_test_count=None, \
                                        restart_checkpointer=True)
                prioritization_module.feedback(element, fail_verdicts)

                fail_verdicts.update({\
                            v: common_mix.GlobalConstants.PASS_TEST_VERDICT \
                                                for v in cannot_cov_tests})
                # put in row format for matrix
                matrix_row_key = element
                matrix_row_values = \
                                {tc:failverdict_to_val_map[fail_verdicts[tc]] \
                                                    for tc in fail_verdicts}
                serialize_on = (pos % serialize_period == 0)
                cp_data[0][matrix_row_key] = matrix_row_values

                if executionoutput is not None:
                    cp_data[1][element] = exec_outs_by_tests

                # @Checkpointing: for time
                if serialize_on and checkpoint_handler is not None:
                    checkpoint_handler.do_checkpoint( \
                                            func_name=cp_calling_func_name, \
                                            taskid=cp_calling_done_task_id, \
                                            tool=cp_calling_tool, \
                                            opt_payload=cp_data)

        # Write the execution data into the matrix
        for matrix_row_key, matrix_row_values in list(cp_data[0].items()):
            matrix.add_row_by_key(matrix_row_key, matrix_row_values, \
                                                            serialize=False)

        # TODO: Make the following two instructions atomic                                                    
        # final serialization (in case #Muts not multiple od serialize_period)
        matrix.serialize()

        # Write the execution output data
        if executionoutput is not None:
            if len(cp_data[1]) > 0:
                executionoutput.add_data(cp_data[1], serialize=True)
            else:
                executionoutput.serialize()
    #~ def _runtest_separate_criterion_program()

    def runtests_criteria_coverage (self, testcases, \
                                    criteria_element_list_by_criteria, \
                                    criterion_to_matrix, \
                                    criterion_to_executionoutput, \
                                    re_instrument_code=True, \
                                    cover_criteria_elements_once=False, \
                                    prioritization_module_by_criteria=None, \
                                    test_parallel_count=1):
        """
            (TODO: support parallelism: per test outdata)
        """
        # FIXME: Support parallelism, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(test_parallel_count <= 1, \
                "FIXME: Must first implement support for parallel mutation")
        #~ FXIMEnd

        # @Checkpoint: create a checkpoint handler (for time)
        cp_func_name = "runtests_criteria_coverage"
        cp_task_id = 1
        checkpoint_handler = CheckPointHandler(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        ERROR_HANDLER.assert_true(len(criterion_to_matrix) > 0, \
                                            "no criterion enabled", __file__)

        ERROR_HANDLER.assert_true(len(set(criterion_to_matrix) - \
                                set(self.get_supported_criteria())) == 0, \
                            "Some unsuported criteria are enabled", __file__)

        ERROR_HANDLER.assert_true(criterion_to_executionoutput is None or \
                set(criterion_to_matrix) == set(criterion_to_executionoutput),\
                "mismatch of criteria between matrix and outlog" , __file__)

        # Check that the result_matrix is empty and fine
        for criterion in criterion_to_matrix:
            ERROR_HANDLER.assert_true( \
                            criterion_to_matrix[criterion].is_empty(), \
                                          "the matrix must be empty", __file__)

            ERROR_HANDLER.assert_true( \
                    set(testcases) == set(criterion_to_matrix[criterion]\
                                                .get_nonkey_colname_list()), \
                        "The specified test cases are not same in the matrix",
                                                                    __file__)

            ERROR_HANDLER.assert_true(\
                        criterion_to_executionoutput[criterion] is None or \
                        criterion_to_executionoutput[criterion].is_empty(), \
                                    "the execoutput must be empty", __file__)

        # @Checkpoint: check 
        if checkpoint_handler.is_to_execute(func_name=cp_func_name, \
                                                            taskid=cp_task_id):
            # Intrument the codes is requested 
            if re_instrument_code:
                self.instrument_code(\
                                enabled_criteria=criterion_to_matrix.keys())

            # @Checkpoint: checkpoint
            checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                                taskid=cp_task_id)

        # @Checkpoint: next task
        cp_task_id += 1

        # Split criteria
        meta_crits = list(set(criterion_to_matrix) & \
                                set(self._get_meta_instrumentation_criteria()))
        separated_crits = list(set(criterion_to_matrix) & \
                        set(self._get_separated_instrumentation_criteria()))

        m_crit2mat, s_crit2mat = self._extract_sub_dicts(criterion_to_matrix,\
                                                [meta_crits, separated_crits])
        if criterion_to_executionoutput is not None:
            m_crit2execout, s_crit2execout = self._extract_sub_dicts(\
                                                criterion_to_executionoutput,\
                                                [meta_crits, separated_crits])
        m_crit2elem, s_crit2elem = self._extract_sub_dicts( \
                                        criteria_element_list_by_criteria,\
                                                [meta_crits, separated_crits])
        m_crit2pm, s_crit2pm = None, None
        if prioritization_module_by_criteria is not None:
            m_crit2pm, s_crit2pm = self._extract_sub_dicts( \
                                            prioritization_module_by_criteria,\
                                                [meta_crits, separated_crits])
        else:
            s_crit2pm = {c: None for c in separated_crits}

        # runtest with the meta files
        if len(m_crit2mat) > 0 and \
                    checkpoint_handler.is_to_execute(func_name=cp_func_name, \
                                            taskid=cp_task_id):
            self._runtest_meta_criterion_program(testcases=testcases, \
                                criterion_to_matrix=m_crit2mat, \
                                criterion_to_executionoutput=m_crit2execout, \
                                criteria_element_list_by_criteria=m_crit2elem,\
                                cover_criteria_elements_once=\
                                            cover_criteria_elements_once,\
                                prioritization_module_by_criteria=m_crit2pm, \
                                test_parallel_count=test_parallel_count)

            # @Checkpoint: checkpoint
            checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                                taskid=cp_task_id)

        # @Checkpoint: next task
        cp_task_id += 1

        # runtest with the separate files
        for criterion in s_crit2mat.keys():
            if checkpoint_handler.is_to_execute(func_name=cp_func_name, \
                                taskid=cp_task_id, tool=criterion.get_str()):
                self._runtest_separate_criterion_program(criterion, \
                                testcases=testcases, \
                                matrix=s_crit2mat[criterion], \
                                executionoutput=s_crit2execout[criterion], \
                                criteria_element_list=s_crit2elem[criterion],\
                                cover_criteria_elements_once=\
                                            cover_criteria_elements_once,\
                                prioritization_module=s_crit2pm[criterion], \
                                test_parallel_count=test_parallel_count, \
                                checkpoint_handler=checkpoint_handler, \
                                cp_calling_func_name=cp_func_name, \
                                cp_calling_done_task_id=(cp_task_id - 1), \
                                cp_calling_tool=criterion.get_str())

                # @Checkpoint: checkpoint
                checkpoint_handler.do_checkpoint(func_name=cp_func_name, \
                                taskid=cp_task_id, tool=criterion.get_str())

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished(None)
    #~ def runtests_criteria_coverage()

    @staticmethod
    def _extract_sub_dicts(dict_obj, in_key_list_list):
        ERROR_HANDLER.assert_true(len(in_key_list_list) > 0, \
                                                    "empty key list", __file__)
        out_dict_list = []
        for key_list in in_key_list_list:
            out_dict_list.append({k: dict_obj[k] for k in key_list})
        return out_dict_list
    #~ def _extract_sub_dicts()

    @staticmethod
    def _get_criteria_groups(criterion2executable_path, \
                                                 criterion2environment_vars):
        """ separate to common executions 
         (those with same exe_path_map and env_vars)
        :return: list of groups, each group info in the tuple
        """
        ERROR_HANDLER.assert_true(set(criterion2executable_path) == \
                        set(criterion2environment_vars), "Missmatch", __file__)
        criterialist = list(criterion2executable_path.keys())
        groups = []
        visited = set()
        for c_pos, criterion in enumerate(criterialist):
            if criterion not in visited:
                # add its group
                groups.append(([criterion], \
                                    criterion2executable_path[criterion],
                                    criterion2environment_vars[criterion]))
                visited.add(criterion)
                # add anything else from same group
                for e_pos in range(c_pos+1, len(criterialist)):
                    if criterion2executable_path[criterialist[e_pos]] == \
                                            groups[-1][1] and \
                            criterion2environment_vars[criterialist[e_pos]] ==\
                                                        groups[-1][2]:
                       groups[-1][0].append(criterialist[e_pos]) 
                       visited.add(criterialist[e_pos])
        return groups
    #~ def _get_criteria_groups()

    def instrument_code (self, enabled_criteria, exe_path_map=None, \
                                code_builds_factory_override=None, \
                                parallel_count=1):
        '''
            (TODO: support parallelism: per test outdata)
        '''

        logging.debug("# Instrumenting code with {} ...".format(\
                                        self.config.get_tool_config_alias()))

        # FIXME: Support parallelism, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(parallel_count <= 1, \
                "FIXME: Must first implement support for parallel mutatio")
        #~ FXIMEnd

        # @Checkpoint: create a checkpoint handler (for time)
        checkpoint_handler = CheckPointHandler(self.get_checkpointer())
        if not checkpoint_handler.is_finished():

            ERROR_HANDLER.assert_true(len(enabled_criteria) > 0, \
                                        "no criterion is enabled", __file__)

            if code_builds_factory_override is None:
                code_builds_factory_override = self.code_builds_factory
            
            if exe_path_map is None:
                exe_path_map = code_builds_factory_override.repository_manager\
                                                            .get_exe_path_map()

            self._do_instrument_code ( \
                            exe_path_map=exe_path_map, \
                            code_builds_factory=code_builds_factory_override, \
                            enabled_criteria=enabled_criteria, \
                            parallel_count=parallel_count)

            # @Checkpoint: Finished (for time)
            checkpoint_handler.set_finished(None)
    #~ def instrument_code()

    def _get_latest_top_output_dir(self):
        return os.path.dirname(os.path.dirname(self.criteria_working_dir))
    #~ def _get_latest_top_output_dir()

    def _extract_metaoutlog_data_of_a_test(self, enabled_criteria, \
                                    test_execution_verdict, result_dir_tmp):
        """ Override this in a tool that suports it
            By default it is not supported and thus fails
        """
        ERROR_HANDLER.assert_true("meta outlog unsupported by this tool")
        return {}
    #~ def _extract_metaoutlog_data_of_a_test()
        
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
            ret,_,_ = DriversUtils.execute_and_get_retcode_out_err('sudo', \
                                        ['chmod 777 -R {}'.format(dirpath)])
            ERROR_HANDLER.assert_true(ret == 0, \
                        "'sudo chmod 777 -R "+dirpath+"' failed (returned "+\
                                                        str(ret)+")", __file__)
    #~ def _dir_chmod777()

    #######################################################################
    ##################### Methods to implement ############################
    #######################################################################

    #@abc.abstractclassmethod
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

    @classmethod
    @abc.abstractclassmethod
    def _get_meta_instrumentation_criteria(cls):
        """ Criteria where all elements are instrumented in same file
            :return: list of citeria
        """
        #return [
        #        TestCriteria.STATEMENT_COVERAGE,
        #        TestCriteria.BRANCH_COVERAGE,
        #        TestCriteria.FUNCTION_COVERAGE,
        #       ]
        print ("!!! Must be implemented in child class !!!")
    #~ def _get_meta_instrumentation_criteria()

    @classmethod
    @abc.abstractclassmethod
    def _get_separated_instrumentation_criteria(cls):
        """ Criteria where all elements are instrumented in different files
            :return: list of citeria
        """
        #return [TestCriteria.STRONG_MUTATION]
        print ("!!! Must be implemented in child class !!!")
    #~ def _get_separated_instrumentation_criteria()

    @abc.abstractmethod
    def get_instrumented_executable_paths_map(self, enabled_criteria):
        print ("!!! Must be implemented in child class !!!")
    #~ def get_instrumented_executable_paths_map()

    @abc.abstractmethod
    def get_criterion_info_object(self, criterion):
        print ("!!! Must be implemented in child class !!!")
    #~ def get_criterion_info_object(self, criterion)

    @abc.abstractmethod
    def _get_criterion_element_executable_path(self, criterion, element_id):
        print ("!!! Must be implemented in child class !!!")
    #~ def _get_criterion_element_executable_path

    @abc.abstractmethod
    def _get_criterion_element_environment_vars(self, criterion, element_id):
        '''
            return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _get_criterion_element_environment_vars()

    @abc.abstractmethod
    def _get_criteria_environment_vars(self, result_dir_tmp, enabled_criteria):
        '''
        return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _get_criteria_environment_vars()

    @abc.abstractmethod
    def _collect_temporary_coverage_data(self, criteria_name_list, \
                                            test_execution_verdict, \
                                            used_environment_vars, \
                                            result_dir_tmp, \
                                            testcase):
        '''
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _collect_temporary_coverage_data()

    @abc.abstractmethod
    def _extract_coverage_data_of_a_test(self, enabled_criteria, \
                                    test_execution_verdict, result_dir_tmp):
        '''
            return: the dict of statements with covering count
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _extract_coverage_data_of_a_test()

    @abc.abstractmethod
    def _do_instrument_code (self, exe_path_map, code_builds_factory, \
                                        enabled_criteria, parallel_count=1):
        print ("!!! Must be implemented in child class !!!")
    #~ def _do_instrument_code()
#~ class BaseCriteriaTool
