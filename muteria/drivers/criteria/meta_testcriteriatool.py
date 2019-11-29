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

from muteria.drivers.criteria.criteria_info import CriteriaToInfoObject

from muteria.drivers.criteria import CriteriaToolType, TestCriteria

ERROR_HANDLER = common_mix.ErrorHandler

class MetaCriteriaTool(object):
    '''
    '''
    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"

    @classmethod
    def get_toolnames_by_types_by_criteria_by_language(cls):
        """ get imformation about the plugged-in criteria tool drivers.
            :return: a dict having the form:
                    {
                        language: {
                            criterion: {
                                CriteriaToolType: [
                                    (toolname, is_installed?)
                                ]
                            }
                        }
                    }
        """
        modules_dict = ToolsModulesLoader.get_tools_modules( \
                                            ToolsModulesLoader.CRITERIA_TOOLS)
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
        self.language = language.lower()
        self.meta_test_generation_obj = meta_test_generation_obj
        self.criteria_working_dir = criteria_working_dir
        self.code_builds_factory = code_builds_factory
        self.tools_config_by_criterion_dict = tools_config_by_criterion_dict
        
        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.criteria_working_dir is not None, \
                            "Must specify criteria_working_dir", __file__)
        for criterion in self.tools_config_by_criterion_dict:
            ERROR_HANDLER.assert_true( \
                    len(self.tools_config_by_criterion_dict[criterion]) == \
                    len(set([c.get_tool_config_alias() for c in \
                        self.tools_config_by_criterion_dict[criterion]])), \
                    "some tool configs appear multiple times for {}".format( \
                                                        criterion), __file__)
        
        # Set Indirect Arguments Variables
        self.checkpoints_dir = os.path.join(self.criteria_working_dir, \
                                                            "_checkpoints_")
        self.criteria_info_file_by_criteria = {}
        for criterion in self.tools_config_by_criterion_dict:
            self.criteria_info_file_by_criteria[criterion] = os.path.join(\
                                        self.criteria_working_dir, \
                                        criterion.get_str()+"_info_file.json")


        # Verify indirect Arguments Variables

        # Initialize Other Fields
        self.criteria_configured_tools = {}
        self.checkpointer = None
        
        # Make Initialization Computation
        ## Create dirs
        if not os.path.isdir(self.criteria_working_dir):
            self.clear_working_dir()

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
            for toolconf in self.tools_config_by_criterion_dict[criterion]:
                toolalias = toolconf.get_tool_config_alias()
                if criterion not in self.criteria_configured_tools[toolalias]\
                                [self.TOOL_OBJ_KEY].get_supported_criteria():
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

    def check_tools_installed(self):
        non_installed = []
        for toolalias, tool_obj in self.criteria_configured_tools.items():
            if not tool_obj[self.TOOL_OBJ_KEY].tool_installed():
                non_installed.append(toolalias)
        if len(non_installed) > 0:
            ERROR_HANDLER.error_exit("{}: {}".format(\
                            "The following Criteria tools are not installed", \
                            str(non_installed)))
    #~ def check_tools_installed()

    def clear_working_dir(self):
        if os.path.isdir(self.criteria_working_dir):
            shutil.rmtree(self.criteria_working_dir)
        os.mkdir(self.criteria_working_dir)
        if os.path.isdir(self.checkpoints_dir):
            shutil.rmtree(self.checkpoints_dir)
        os.mkdir(self.checkpoints_dir)
        for _, tool_dat in list(self.criteria_configured_tools.items()):
            tool_dat[self.TOOL_OBJ_KEY].clear_working_dir()
    #~ def clear_working_dir()    

    def _get_tool2criteria(self, criteria_passed):
        ''' TODO: update users of this function
            Take a list of criteria and group by tools
        :param criteria_passed: list representing a criteria considered 
        :return: return the criteria by tools
        '''
        tool2criteria = {}
        for criterion in criteria_passed:
            for config in self.tools_config_by_criterion_dict[criterion]:
                ctoolalias = config.get_tool_config_alias()
                if ctoolalias not in tool2criteria:
                    tool2criteria[ctoolalias] = []
                tool2criteria[ctoolalias].append(criterion)
        return tool2criteria
    #~ def _get_tool2criteria()
                                            
    def runtests_criteria_coverage (self, testcases, criterion_to_matrix, \
                                    criterion_to_executionoutput=None,
                                    criteria_element_list_by_criteria=None, \
                                    re_instrument_code=False, \
                                    cover_criteria_elements_once=False,
                                    prioritization_module_by_criteria=None,
                                    parallel_count=1, \
                                    parallel_criteria_test_scheduler=None,\
                                    restart_checkpointer=False, \
                                    finish_destroy_checkpointer=True):
        ''' 
        Executes the instrumented executable code with testscases and
        returns the different code coverage matrices.

        :param testcases: list of testcases to execute

        :param criterion_to_matrix: dict of <criterion, Matrix file 
                        where to store coverage>. 
        :param criterion_to_executionoutput: dict of <criterion, execoutput 
                        file where to store coverage>. 
        
        :param criteria_element_list_by_criteria: dictionary representing the
                        list of criteria elements (stmts, branches, mutants)
                        to consider in the test execution matices. 
                        Key is the criterion and the value the list of elements

        :param re_instrument_code: Decide whether to instrument code before 
                        running the tests. (Example when instrumentation was 
                        not specifically called. This is True by default)

        :param cover_criteria_elements_once: Specify whether to cover criteria
                        elements once is enough, meaning that we stop 
                        analysing a criterion element once a test covers it.
                        The remaining test covering verdict will be UNKNOWN. 

        :param prioritization_module_by_criteria: dict of prioritization module
                        by criteria. None means no prioritization used.

        :type \parallel_count:
        :param \parallel_count:

        :type \parallel_criteria_test_scheduler:
        :param \parallel_criteria_test_scheduler: scheduler that organize 
                        parallelism across criteria tools.
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
        ERROR_HANDLER.assert_true(parallel_criteria_test_scheduler is None, \
            "Must implement parallel codes tests execution support here", \
                                                                    __file__)
        #~FIXMEnd

        # Check arguments Validity
        ERROR_HANDLER.assert_true(parallel_count > 0, \
                    "invalid parallel  execution count: {}. {}".format( \
                                    parallel_count, "must be >= 1"))

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "runtests_criteria_coverage"
        cp_task_id = 1
        checkpoint_handler = CheckPointHandler( \
                                            self.get_checkpoint_state_object())
        if restart_checkpointer:
            checkpoint_handler.restart()
        if checkpoint_handler.is_finished():
            return

        ERROR_HANDLER.assert_true(len(criterion_to_matrix) > 0, \
                                        "no criterion is enabled", __file__)

        ERROR_HANDLER.assert_true(len(set(criterion_to_matrix) - \
                            set(self.tools_config_by_criterion_dict)) == 0, \
                    "Passed matrices output are more than tool specified", \
                                                                    __file__)

        if criterion_to_executionoutput is not None:
            ERROR_HANDLER.assert_true(set(criterion_to_matrix) == \
                                        set(criterion_to_executionoutput), \
                            "criteria mismatch between matrix and output", \
                                                                    __file__)

        tool2criteria = self._get_tool2criteria(criterion_to_matrix.keys())

        matrices_dir_tmp = os.path.join(self.criteria_working_dir, \
                                                            "codecov_dir.tmp")
        if os.path.isdir(matrices_dir_tmp):
            if restart_checkpointer:
                shutil.rmtree(matrices_dir_tmp)
                os.mkdir(matrices_dir_tmp)
        else:
            os.mkdir(matrices_dir_tmp)

        if criteria_element_list_by_criteria is None:
            criteria_element_list_by_criteria = \
                                        {c: None for c in criterion_to_matrix}

        # get criteria elements by tools
        criteria_elem_list_by_tool = {}
        for criterion in criteria_element_list_by_criteria:
            if criteria_element_list_by_criteria[criterion] is None:
                for t_conf in self.tools_config_by_criterion_dict[criterion]:
                    toolalias = t_conf.get_tool_config_alias()
                    if toolalias not in criteria_elem_list_by_tool:
                        criteria_elem_list_by_tool[toolalias] = {}
                    criteria_elem_list_by_tool[toolalias][criterion] = None
                continue

            criteria_elem_list_by_tool[criterion] = {}
            for crit_elem in criteria_element_list_by_criteria[criterion]:
                toolalias, elem = DriversUtils.reverse_meta_element(crit_elem)
                if toolalias not in criteria_elem_list_by_tool:
                    criteria_elem_list_by_tool[toolalias] = {}
                if criterion not in criteria_elem_list_by_tool[toolalias]:
                    criteria_elem_list_by_tool[toolalias][criterion] = []
                criteria_elem_list_by_tool[toolalias][criterion].append(elem)

            ERROR_HANDLER.assert_true(len(set(criteria_elem_list_by_tool) - \
                                set(self.criteria_configured_tools)) == 0, \
                                "some tool in data not registered", __file__)

        crit2tool2matrixfile = {cv: {} for cv in criterion_to_matrix}
        crit2tool2outhashfile = {cv: {} for cv in criterion_to_executionoutput}
        for ctoolalias in tool2criteria:
            _criteria2matrix = {}
            _criteria2outhash = {}
            for criterion in tool2criteria[ctoolalias]:
                _criteria2matrix[criterion] = os.path.join(matrices_dir_tmp, \
                                                criterion.get_field_value() 
                                                                + '-' 
                                                                + ctoolalias 
                                                                + '.csv')
                if criterion_to_executionoutput is None or \
                            criterion_to_executionoutput[criterion] is None:
                    _criteria2outhash[criterion] = None
                else:
                    _criteria2outhash[criterion] = \
                                            os.path.join(matrices_dir_tmp, \
                                                criterion.get_field_value() 
                                                        + '-' 
                                                        + ctoolalias 
                                                        + '.outloghash.json')
                crit2tool2matrixfile[criterion][ctoolalias] = \
                                                    _criteria2matrix[criterion]
                crit2tool2outhashfile[criterion][ctoolalias] = \
                                                _criteria2outhash[criterion]

            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias):
                for criterion in _criteria2matrix:
                    _criteria2matrix[criterion] = \
                                        common_matrices.ExecutionMatrix( \
                                        filename=_criteria2matrix[criterion], \
                                        non_key_col_list=testcases)
                    if _criteria2outhash[criterion] is not None:
                        _criteria2outhash[criterion] = \
                                        common_matrices.OutputLogData( \
                                        filename=_criteria2outhash[criterion])
                # Actual execution
                ctool = self.criteria_configured_tools[ctoolalias][\
                                                            self.TOOL_OBJ_KEY]
                ctool.runtests_criteria_coverage(testcases, \
                                criteria_element_list_by_criteria=\
                                        criteria_elem_list_by_tool[toolalias],\
                                criterion_to_matrix=_criteria2matrix, \
                                criterion_to_executionoutput=\
                                                            _criteria2outhash,\
                                re_instrument_code=re_instrument_code, \
                                cover_criteria_elements_once=\
                                                cover_criteria_elements_once, \
                                prioritization_module_by_criteria=\
                                            prioritization_module_by_criteria)

                # Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias)

        # Aggregate the matrices and out hashes
        ## Create reult matrices and out hashes
        result_matrices = {}
        result_outloghashes = {}
        for criterion in criterion_to_matrix:
            result_matrices[criterion] = common_matrices.ExecutionMatrix( \
                                filename=criterion_to_matrix[criterion], \
                                non_key_col_list=testcases)
            if criterion_to_executionoutput[criterion] is None:
                result_outloghashes[criterion] = None
            else:
                result_outloghashes[criterion] = \
                            common_matrices.OutputLogData(filename=\
                                    criterion_to_executionoutput[criterion])
                ERROR_HANDLER.assert_true(\
                            crit2tool2outhashfile[criterion] is not None,
                            "Bug: log enabled but hidden from tool", __file__)
        ## Actual aggregate
        for criterion in result_matrices:
            result_matrix = result_matrices[criterion]
            result_outloghash = result_outloghashes[criterion]
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
                key2nonkeydict = tool_matrix.to_pandas_df().\
                        set_index(tool_matrix.get_key_colname(), drop=True).\
                                                to_dict(orient="index")
                
                for c_key in key2nonkeydict:
                    meta_c_key = DriversUtils.make_meta_element(\
                                                        str(c_key), mtoolalias)
                    result_matrix.add_row_by_key(meta_c_key, 
                                                        key2nonkeydict[c_key], 
                                                        serialize=False)

                # out log hash
                if crit2tool2outhashfile[criterion] is not None:
                    tool_outloghash = common_matrices.OutputLogData(\
                            filename=\
                                crit2tool2outhashfile[criterion][mtoolalias])
                    for objective, objective_data in \
                                tool_outloghash.get_zip_objective_and_data():
                        meta_objective = DriversUtils.make_meta_element(\
                                                    str(objective), mtoolalias)
                        result_outloghash.add_data(
                                            {meta_objective: objective_data}, \
                                            serialize=False)

            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id + 1,
                                        tool=criterion.get_str()):
                # Serialized the computed matrix
                result_matrix.serialize()
                if result_outloghash is not None:
                    result_outloghash.serialize()
            # @Checkpoint: Checkpointing
            checkpoint_handler.do_checkpoint( \
                                    func_name=cp_func_name, \
                                    taskid=cp_task_id + 1,
                                    tool=criterion.get_str())
        
        # Delete the temporary tool matrix's directory
        if os.path.isdir(matrices_dir_tmp):
            shutil.rmtree(matrices_dir_tmp)

        # @Checkpoint: Finished
        detailed_exectime = {}
        for ctoolalias in tool2criteria:
            ct = self.criteria_configured_tools[ctoolalias][self.TOOL_OBJ_KEY]
            detailed_exectime[ctoolalias] = (\
                        ct.get_checkpointer().get_execution_time(),\
                        ct.get_checkpointer().get_detailed_execution_time())

        checkpoint_handler.set_finished(\
                                    detailed_exectime_obj=detailed_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()
    #~ def runtests_criteria_coverage()

    def instrument_code (self, criteria_enabled_list=None, \
                    exe_path_map=None, \
                    #outputdir_override=None, \
                    #code_builds_factory_override=None, \
                    parallel_count=1, \
                    restart_checkpointer=False, \
                    finish_destroy_checkpointer=True):
        """ Instrument the code for the criteria measurements. 

        :type criteria_enabled_list: dict or None
        :param criteria_enabled_list: When None, use all supported criteria
                    else use the specified criteria
    
        :type \exe_path_map: dict or None
        :param \exe_path_map: When None, use all exe, else instrument 
                    files as dict key and write the instrumented output
                    in directory as value. 
    
        :type \parallel_count:
        :param \parallel_count:
    
        :type \restart_checkpointer:
        :param \restart_checkpointer:
    
        :type \finish_destroy_checkpointer:
        :param \finish_destroy_checkpointer:
    
        :raises:
    
        :rtype:
        """
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

        if criteria_enabled_list is None:
            criteria_enabled_list = self.tools_config_by_criterion_dict.keys()
        else:
            ERROR_HANDLER.assert_true(len(criteria_enabled_list) > 0, \
                                        "no criterion is enabled", __file__)

            ERROR_HANDLER.assert_true(len(set(criteria_enabled_list) - \
                            set(self.tools_config_by_criterion_dict)) == 0, \
                        "Passed matrice output are more than toll specified", \
                                                                    __file__)

        tool2criteria = self._get_tool2criteria(criteria_enabled_list)

        for ctoolalias in tool2criteria:
            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias):
                # Actual execution
                ctool = self.criteria_configured_tools[ctoolalias][\
                                                            self.TOOL_OBJ_KEY]
                ctool.instrument_code(\
                                enabled_criteria=tool2criteria[ctoolalias],\
                                exe_path_map=exe_path_map)
                # ensure repo is set back
                self.code_builds_factory.set_repo_to_build_default()

                # @Checkpoint: Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolalias)

        # Invalidate any existing mutant info so it can be recomputed
        self._invalidate_criteria_info(
                                enabled_criteria=tool2criteria[ctoolalias])
                                

        # @Checkpoint: Finished
        detailed_exectime = {}
        for ctoolalias in tool2criteria:
            ct = self.criteria_configured_tools[ctoolalias][self.TOOL_OBJ_KEY]
            detailed_exectime[ctoolalias] = (\
                        ct.get_checkpointer().get_execution_time(),\
                        ct.get_checkpointer().get_detailed_execution_time())

        checkpoint_handler.set_finished( \
                                    detailed_exectime_obj=detailed_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()
    #~ def instrument_code()

    def _compute_criterion_info(self, criterion, candidate_tool_aliases=None):
        if criterion not in CriteriaToInfoObject:
            return None

        meta_criterion_info_obj = CriteriaToInfoObject[criterion]()
        if candidate_tool_aliases is None:
            candidate_tool_aliases = []
            for config in self.tools_config_by_criterion_dict[criterion]:
                candidate_tool_aliases.append(config.get_tool_config_alias())
        for ctoolalias in candidate_tool_aliases:
            ctool = self.criteria_configured_tools[ctoolalias]\
                                                            [self.TOOL_OBJ_KEY]
            tool_element_info = ctool.get_criterion_info_object(criterion)
            if tool_element_info is not None:
                old2new_tests = {}
                for c_elem in tool_element_info.get_elements_list():
                    meta_c_key = DriversUtils.make_meta_element(\
                                                            c_elem, ctoolalias)
                    old2new_tests[c_elem] = meta_c_key
                meta_criterion_info_obj.update_using(\
                                                ctoolalias, old2new_tests, \
                                                            tool_element_info)
        return meta_criterion_info_obj
    #~ def _compute_criterion_info()
    
    def get_criterion_info_object(self, criterion):
        if criterion not in CriteriaToInfoObject:
            return None
            
        return CriteriaToInfoObject[criterion]().load_from_file(\
                                    self.get_criterion_info_file(criterion))
    #~ def def get_criterion_info_object()

    def get_criterion_info_file(self, criterion):
        if criterion not in CriteriaToInfoObject:
            return None
            
        # Compute and write the testcase info if not present
        # only place where the meta info is written
        info_file = self._unchecked_get_criterion_info_file(criterion)
        if self._criterion_info_is_invalidated(criterion):
            self._compute_criterion_info(criterion).write_to_file(info_file)
        return info_file
    #~ def get_criterion_info_file()

    def _unchecked_get_criterion_info_file(self, criterion):
        if criterion not in CriteriaToInfoObject:
            return None
            
        return self.criteria_info_file_by_criteria[criterion] 
    #~ def _unchecked_get_criteria_info_file():

    def _invalidate_criterion_info(self, criterion):
        if criterion in CriteriaToInfoObject:
            info_file = self._unchecked_get_criterion_info_file(criterion)
            if os.path.isfile(info_file):
                os.remove(info_file)
    #~ def _invalidate_criterion_info()

    def _invalidate_criteria_info(self, enabled_criteria=None):
        if enabled_criteria is None:
            enabled_criteria = self.tools_config_by_criterion_dict.keys()
        for criterion in enabled_criteria:
            if criterion in CriteriaToInfoObject:
                self._invalidate_criterion_info(criterion)
    #~ def _invalidate_criteria_info()

    def _criterion_info_is_invalidated(self, criterion):
        ERROR_HANDLER.assert_true(criterion in CriteriaToInfoObject,
                            "The criterion {} {}".format(criterion.get_str(), \
                            "must have info Class registered for this"), \
                                                                    __file__)
            
        return not os.path.isfile(\
                            self._unchecked_get_criterion_info_file(criterion))
    #~ def _criterion_info_is_invalidated()

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

    def get_criteria_tools_by_name(self, toolname):
        res = {}
        for alias, data in self.criteria_configured_tools.items():
            if data[self.TOOL_OBJ_KEY].get_toolname() == toolname:
                res[alias] = data[self.TOOL_OBJ_KEY]
        return res
    #~ def get_criteria_tools_by_name()

    def get_checkpoint_state_object(self):
        return self.checkpointer
    #~ def get_checkpoint_state_object()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer()
#~ class MetaCriteriaTool
