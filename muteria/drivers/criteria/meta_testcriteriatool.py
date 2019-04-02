#
# [LICENCE]
#
"""
This module is used through MetaCriteriaTool class
Which access the relevant testcase tools as specified

The tools are organized by programming language
For each language, there is a folder for each tool, 
named after the tool in lowercase

Each criteria tool package have the following in the __init__.py file:
>>> import <Module>.<class extending BaseCriteriaTool> as CriteriaTool
"""

from __future__ import print_function
import os
import sys
import glob
import logging
import shutil

import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from muteria.drivers import ToolsModulesLoader
from muteria.drivers import DriversUtils

from muteria.drivers.checkpoint_handler import CheckPointHandler

from muteria.drivers.criteria.criterion_info import CriterionElementInfoObject

from muteria.drivers.criteria import CriteriaToolType, TestCriteria

ERROR_HANDLER = common_mix.ErrorHandler

class MetaCriteriaTool(object):
    '''
    '''
    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"

    @classmethod
    def get_toolnames_by_types_by_criteria_by_language(cls):
        modules_dict = ToolsModulesLoader.get_tools_modules( \
                                            ToolsModulesLoader.TESTCASES_TOOLS)
        res = {}
        for language in modules_dict:
            res[language] = {}
            for toolname in modules_dict[language]:
                for tooltype in CriteriaToolType:
                    tooltype_name = tooltype.get_field_value()
                    try:
                        # the tooltype is returned by config.get_tool_type()
                        CriteriaTool = getattr(\
                                            modules_dict[language][toolname],\
                                                                tooltype_name)
                        if CriteriaTool is None:
                            continue
                        for criterion in CriteriaTool.get_supported_criteria():
                            if criterion not in res[language]:
                                res[language][criterion] = {}
                            if tooltype_name not in res[language][criterion]:
                                res[language][criterion][tooltype_name] = []
                            res[language][criterion][tooltype_name].append(\
                                        (toolname, CriteriaTool.installed()))
                    except AttributeError:
                        ERROR_HANDLER.error_exit("{} {} {} {}".format( \
                                "(REPORT BUG) The criteria tool of type", \
                                tooltype_name,\
                                "is not present for criteria tool", toolname),\
                                                                    __file__)
        return res
    #~ def get_toolnames_by_types_by_criteria_by_language()

    def __init__(self, language, meta_test_generation_obj, \
                        criteria_working_dir, \
                        code_builds_factory, \
                        tools_config_by_criterion_dict):
        # Set Constants
        self.modules_dict = ToolsModulesLoader.get_tools_modules(\
                                            ToolsModulesLoader.CRITERIA_TOOLS)
        
        # Set Direct Arguments Variables
        self.language = language
        self.meta_test_generation_obj = meta_test_generation_obj
        self.criteria_working_dir = criteria_working_dir
        self.code_builds_factory = code_builds_factory
        self.tools_config_by_criterion_dict = tools_config_by_criterion_dict
        
        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.criteria_working_dir is None, \
                            "Must specify criteria_working_dir", __file__)
        for criterion in self.tools_config_by_criterion_dict:
            ERROR_HANDLER.assert_true( \
                    len(self.tools_config_by_criterion_dict[criterion]) != \
                    len(set([c.get_tool_config_alias() for c in \
                        self.tools_config_by_criterion_dict[criterion]])), \
                    "some tool configs appear multiple times for {}".format( \
                                                        criterion), __file__)
        
        # Set Indirect Arguments Variables
        self.checkpoints_dir = os.path.join(self.criteria_working_dir, \
                                                            "_checkpoints_")
        self.code_info_file = \
            os.path.join(self.criteria_working_dir, "criteria_info_file.json")

        # Verify indirect Arguments Variables

        # Initialize Other Fields
        self.criteria_configured_tools = {}
        self.checkpointer = None
        
        # Make Initialization Computation
        ## Create dirs
        if not os.path.isdir(self.criteria_working_dir):
            self.clear_working_dir()

        if not os.path.isdir(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)

        ## set checkpointer
        self.checkpointer = common_fs.CheckpointState(\
                                                *self._get_checkpoint_files())

        ## Create the different tools
        ### XXX Merge configs that are identical across criteria
        tmp_alias2conf = {}
        for criterion in self.tools_config_by_criterion_dict:
            for config in self.tools_config_by_criterion_dict[criterion]:
                toolname = config.get_tool_name()
                toolalias = config.get_tool_config_alias()
                if toolalias in tmp_alias2conf:
                    # make sure that the config is the same
                    ERROR_HANDLER.assert_true(config == \
                                                tmp_alias2conf[toolalias], \
                                        "{} {} {}".format( \
                                    "same tool alias but different", \
                                "config for alias", toolalias), __file__)
                else:
                    tmp_alias2conf[toolalias] = config
                    tool_working_dir = self._get_criteria_tool_out_folder(\
                                                                    toolalias)
                    tool_checkpointer = common_fs.CheckpointState( \
                            *self._get_criteria_tool_checkpoint_files( \
                                                                    toolalias))
                    self.checkpointer.add_dep_checkpoint_state( \
                                                            tool_checkpointer)
                    self.criteria_configured_tools[toolalias] = {
                        self.TOOL_OBJ_KEY: self._create_criteria_tool( \
                                                    toolname, \
                                                    tool_working_dir, config, \
                                                    tool_checkpointer),
                        self.TOOL_WORKDIR_KEY: tool_working_dir,
                    }

        # verify supported criteria
        for criterion in self.tools_config_by_criterion_dict:
            for toolalias in self.tools_config_by_criterion_dict[criterion]\
                                                    .get_tool_config_alias():
                if criterion not in \
                                self.criteria_configured_tools[toolalias].\
                                                    get_supported_criteria():
                    ERROR_HANDLER.error_exit( \
                            "tool {} specified for unsupported criterion {}".\
                                        format(toolalias, criterion), __file__)
    #~ def __init__()

    def _create_criteria_tool(self, toolname, tool_working_dir, \
                                                    config, tool_checkpointer):
        '''

        '''
        ERROR_HANDLER.assert_true( \
            toolname in self.modules_dict[self.language],
            "Invalid toolname given: {}".format(toolname), __file__)
        try:
            # the tooltype is returned by config.get_tool_type()
            CriteriaTool = getattr( \
                                self.modules_dict[self.language][toolname],\
                                    config.get_tool_type().get_field_value())
        except AttributeError:
            ERROR_HANDLER.error_exit("{} {} {} {}".format( \
                                "(REPORT BUG) The Criteria tool of type", \
                                config.get_tool_type().get_field_value(),\
                                "is not present for test tool", toolname), \
                                                                    __file__)

        ERROR_HANDLER.assert_true(CriteriaTool is not None, \
                                "The {} language's tool {} {} {}.".format( \
                                self.language, toolname, \
                            "does not implement the criteria tool type", \
                                config.get_tool_type().get_str()), __file__)
        crit_tool = CriteriaTool(self.meta_test_generation_obj, \
                                                tool_working_dir, \
                                                self.code_builds_factory, \
                                                    config, tool_checkpointer)
        return crit_tool
    #~ def _create_criteria_tool()

    def clear_working_dir(self):
        if os.path.isdir(self.criteria_working_dir):
            shutil.rmtree(self.criteria_working_dir)
        os.mkdir(self.criteria_working_dir)
    #~ def clear_working_dir()    

    def _get_tool2criteria_values(self, criteria_passed_values):
        ''' TODO: check this to only care about passed criteria and update users
        Take values by criteria and return values by tools. This map the
        criteria to the correspondng tools to have each tool linked to its
        representing criteria which are further linked to the object values.

        :param criteria_passed_values: dict representing a certain object 
                value by criterion (value for each criterion)
        :return: return the object values by tools
        '''
        none_activated_default = {c: None for c in list(TestCriteria)}
        tool2criteria_values = {}
        for criterion in criteria_passed_values:
            for config in self.tools_config_by_criterion_dict[criterion]:
                ctoolalias = config.get_tool_config_alias()
                if ctoolalias not in tool2criteria_values:
                    tool2criteria_values[ctoolalias] = \
                                                none_activated_default.copy()
                tool2criteria_values[ctoolalias][criterion] = \
                                            criteria_passed_values[criterion]
        return tool2criteria_values
    #~ def _get_tool2criteria_values()
                                            
    def runtests_code_coverage (self, testcases, re_instrument_code=True, \
                                        statement_matrix=None, \
                                        branch_matrix=None, \
                                        function_matrix=None, \
                                        parallel_count=1, \
                                        parallel_mutant_test_scheduler=None, \
                                        restart_checkpointer=False, \
                                        finish_destroy_checkpointer=True):
        '''
        Executes the instrumented executable code with testscases and
        returns the different code coverage matrices.

        :param testcases: list of testcases to execute
        :param re_instrument_code: Decide whether to instrument code before 
                        running the tests. (Example when instrumentation was 
                        not specifically called. This is True by default)
        :param statement_matrix: Matrix object where to store statement 
                        coverage. If None, statement coverage is disabled
        :param branch_matrix: Matrix object where to store branch 
                        coverage. If None, branch coverage is disabled
        :param function_matrix: Matrix object where to store function 
                        coverage. If None, function coverage is disabled

        :type \parallel_count:
        :param \parallel_count:

        :type \parallel_mutant_test_scheduler:
        :param \parallel_mutant_test_scheduler:
                        (TODO: Implement support)

        :type \restart_checkpointer:
        :param \restart_checkpointer:

        :type finish_destroy_checkpointer:
        :param finish_destroy_checkpointer:
        '''

        # FIXME: Make sure that the support are implemented for 
        # parallelism and test prioritization. Remove the code bellow 
        # once supported:
        ERROR_HANDLER.assert_true(parallel_count <= 1, \
                    "Must implement parallel execution support here", \
                                                                    __file__)
        ERROR_HANDLER.assert_true(parallel_mutant_test_scheduler is None, \
            "Must implement parallel codes tests execution support here", \
                                                                    __file__)
        #~FIXMEnd

        # Check arguments Validity
        ERROR_HANDLER.assert_true(parallel_count > 0, \
                    "invalid parallel  execution count: {}. {}".format( \
                                    parallel_count, "must be >= 1"))

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "runtests_code_coverage"
        cp_task_id = 1
        checkpoint_handler = CheckPointHandler( \
                                            self.get_checkpoint_state_object())
        if restart_checkpointer:
            checkpoint_handler.restart()
        if checkpoint_handler.is_finished():
            return

        ERROR_HANDLER.assert_true(statement_matrix is not None \
                                    or branch_matrix is not None \
                                    or function_matrix is not None, \
                                        "no criterion is enabled", __file__)
        criteria_passed_values = {}
        criteria_passed_values[TestCriteria.STATEMENT_COVERAGE] = \
                                                            statement_matrix
        criteria_passed_values[TestCriteria.BRANCH_COVERAGE] = branch_matrix
        criteria_passed_values[TestCriteria.FUNCTION_COVERAGE] = function_matrix

        ERROR_HANDLER.assert_true(len(set(criteria_passed_values) - \
                            set(self.tools_config_by_criterion_dict)) == 0, \
                    "Passed matrices output are more than tool specified", \
                                                                    __file__)

        tool2criteria_values = self._get_tool2criteria_values( \
                                                        criteria_passed_values)

        matrices_dir_tmp = os.path.join(self.criteria_working_dir, \
                                                            "codecov_dir.tmp")
        if os.path.isdir(matrices_dir_tmp):
            if restart_checkpointer:
                shutil.rmtree(matrices_dir_tmp)
                os.mkdir(matrices_dir_tmp)
        else:
            os.mkdir(matrices_dir_tmp)

        crit2tool2matrixfile = {cv: {} for cv in criteria_passed_values \
                                    if criteria_passed_values[cv is not None]}
        for ctoolalias in tool2criteria_values:
            criteria2matrix = {}
            for criterion in tool2criteria_values[ctoolalias]:
                if tool2criteria_values[ctoolalias][criterion] is not None:
                    criteria2matrix[criterion] = \
                                crit2tool2matrixfile[criterion][ctoolalias] = \
                                            os.path.join(matrices_dir_tmp, \
                                                criterion.get_field_value()\
                                                    +'-'+ctoolalias+'.csv')
                else:
                    criteria2matrix[criterion] = \
                            crit2tool2matrixfile[criterion][ctoolalias] = None

            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias):
                for criterion in criteria2matrix:
                    if criteria2matrix[criterion] is not None:
                        criteria2matrix[criterion] = \
                                        common_matrices.ExecutionMatrix( \
                                        filename=criteria2matrix[criterion])
                # Actual execution
                ctool = self.criteria_configured_tools[ctoolalias][\
                                                            self.TOOL_OBJ_KEY]
                ctool.runtests_code_coverage(testcases, \
                        criterion_to_matrix=criteria2matrix,\
                        re_instrument_code=re_instrument_code)

                # Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias)

        # Aggregate the matrices
        ## Create reult matrices
        result_matrices = {}
        for criterion in criteria_passed_values:
            if criteria_passed_values[criterion] is not None:
                result_matrices[criterion] = common_matrices.ExecutionMatrix( \
                                    filename=criteria_passed_values[criterion])
        ## Actual aggregate
        for criterion in result_matrices:
            result_matrix = result_matrices[criterion]
            ERROR_HANDLER.assert_true( \
                            crit2tool2matrixfile[criterion] is not None, \
                        "Criterion was not considered before (BUG)", __file__)
            for mtoolalias in crit2tool2matrixfile[criterion]:
                tool_matrix = common_matrices.ExecutionMatrix(\
                        filename=crit2tool2matrixfile[criterion][mtoolalias])

                # Check columns
                ERROR_HANDLER.assert_true(tool_matrix.get_key_colname() == \
                                            result_matrix.get_key_colname(), \
                                    "mismatch on key column name", __file__)
                ERROR_HANDLER.assert_true( \
                                set(tool_matrix.get_nonkey_colname_list()) == \
                                set(result_matrix.get_nonkey_colname_list()), \
                                "mismatch on non key column names", __file__)

                # bring in the data
                key2nonkeydict = tool_matrix.get_pandas_df().\
                            set_index(tool_matrix.get_key_colname, drop=True).\
                                                to_dict(orient="index")
                for c_key in key2nonkeydict:
                    meta_c_key = \
                            DriversUtils.make_meta_element(c_key, mtoolalias)
                    result_matrix.add_row_by_key(meta_c_key, 
                                                        key2nonkeydict[c_key], 
                                                        serialize=False)

            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id + 1,
                                        tool=criterion):
                # Serialized the computed matrix
                result_matrix.serialize()
            # @Checkpoint: Checkpointing
            checkpoint_handler.do_checkpoint( \
                                    func_name=cp_func_name, \
                                    taskid=cp_task_id + 1,
                                    tool=criterion)
        
        # Delete the temporary tool matrix's directory
        if os.path.isdir(matrices_dir_tmp):
            shutil.rmtree(matrices_dir_tmp)

        # @Checkpoint: Finished
        detailed_exectime = {ct: ct.get_checkpointer().get_execution_time() \
                                                for ct in tool2criteria_values}
        checkpoint_handler.set_finished(\
                                    detailed_exectime_obj=detailed_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()
    #~ def runtests_code_coverage()

    def instrument_code (self, outputdir=None, \
                    code_builds_factory_override=None, \
                    statement_enabled=MetaCriteriaTool.STATEMENT_DEFAULT, \
                    branch_enabled=MetaCriteriaTool.BRANCH_DEFAULT, \
                    function_enabled=MetaCriteriaTool.FUNCTION_DEFAULT, \
                    parallel_count=1, \
                    restart_checkpointer=False, \
                    finish_destroy_checkpointer=True):
        '''
        '''
        # FIXME: Support parallelism, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(parallel_count <= 1, \
                "FIXME: Must first implement support for parallel")
        #~ FXIMEnd

        # Check arguments Validity
        ERROR_HANDLER.assert_true(parallel_count > 0, \
                    "invalid parallel  execution count: {}. {}".format( \
                            parallel_count, "must be >= 1"), __file__)

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "instrument_code"
        cp_task_id = 1
        checkpoint_handler = CheckPointHandler( \
                                            self.get_checkpoint_state_object())
        if restart_checkpointer:
            checkpoint_handler.restart()
        if checkpoint_handler.is_finished():
            return

        ERROR_HANDLER.assert_true(statement_enabled or branch_enabled or \
                        function_enabled, "no criterion is enabled", __file__)

        criteria_passed_values = {}
        criteria_passed_values[TestCriteria.STATEMENT_COVERAGE] = \
                                                            statement_enabled
        criteria_passed_values[TestCriteria.BRANCH_COVERAGE] = branch_enabled
        criteria_passed_values[TestCriteria.FUNCTION_COVERAGE] = \
                                                            function_enabled

        ERROR_HANDLER.assert_true(len(set(criteria_passed_values) - \
                            set(self.tools_config_by_criterion_dict)) == 0, \
                "Passed matrice output are more than toll specified", __file__)

        tool2criteria_values = self._get_tool2criteria_values( \
                                                        criteria_passed_values)

        for ctoolalias in tool2criteria_values:
            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias):
                # Actual execution
                ctool = self.criteria_configured_tools[ctoolalias][\
                                                            self.TOOL_OBJ_KEY]
                ctool.instrument_code(outputdir, code_builds_factory_override,\
                        criterion_to_enabling=tool2criteria_values[ctoolalias])

                # @Checkpoint: Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias)

        # @Checkpoint: Finished
        detailed_exectime = {ct: ct.get_checkpointer().get_execution_time() \
                                                for ct in tool2criteria_values}
        checkpoint_handler.set_finished( \
                                    detailed_exectime_obj=detailed_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()
    #~ def instrument_code()

    def _get_criteria_tool_out_folder(self, ccov_toolname, top_outdir=None):
        if top_outdir is None:
            top_outdir = self.criteria_working_dir
        return os.path.join(top_outdir, ccov_toolname)
    #~def _get_criteria_tool_out_folder()

    def _get_criteria_tool_checkpoint_files(self, criteria_toolname, \
                                                    top_checkpoint_dir=None):
        if top_checkpoint_dir is None:
            top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                        criteria_toolname+"_checkpoint.state"+suffix) \
                        for suffix in ("", ".backup")]
    #~def _get_criteria_tool_checkpoint_files()
        
    def _get_checkpoint_files(self):
        top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                        "checkpoint.state"+suffix) \
                        for suffix in ("", ".backup")]
    #~def _get_checkpoint_files()

    def get_checkpoint_state_object(self):
        return self.checkpointer
    #~ def get_checkpoint_state_object()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer()
#~ class MetaCriteriaTool
