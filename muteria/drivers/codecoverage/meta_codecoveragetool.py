# TODO Fix the call of sub tool by toolname
# TODO also fix duplucation in __init__ for tool with many criteria

# This module is used through MetaCodecoverageTool class
# Which access the relevant testcase tools as specified

# The tools are organized by programming language
# For each language, there is a folder for each tool, 
# named after the tool in lowercase

# Each codecoverage tool package have the following in the __init__.py file:
# import <Module>.<class extending BaseCodecoverageTool> as CodecoverageTool

from __future__ import print_function
import os
import sys
import glob
import logging

import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from base_codecoveragetool import BaseCodecoverageTool

from ... import ToolsModulesLoader

from ...checkpoint_handler import CheckpointHandlerForMeta

ERROR_HANDLER = common_mix.ErrorHandler

class MetaCodecoverageTool(object):
    '''
    '''

    STATEMENT_DEFAULT = True
    BRANCH_DEFAULT = True
    FUNCTION_DEFAULT = True

    STATEMENT_KEY = BaseCodecoverageTool.STATEMENT_KEY
    BRANCH_KEY = BaseCodecoverageTool.BRANCH_KEY
    FUNCTION_KEY = BaseCodecoverageTool.FUNCTION_KEY

    CRITERIA_LIST = [STATEMENT_KEY, BRANCH_KEY, FUNCTION_KEY]

    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"

    def __init__(self, meta_test_generation_obj, codecoverage_working_dir, 
                                                tools_by_criterion_dict,
                                                code_builder, config_dict):
        self.modules_dict = ToolsModulesLoader.get_tools_modules(
                                    ToolsModulesLoader.CODE_COVERAGE_TOOLS)
        self.meta_test_generation_obj = meta_test_generation_obj
        sefl.codecoverage_working_dir = codecoverage_working_dir
        self.tools_by_criterion_dict = tools_by_criterion_dict
        self.code_builder = code_builder
        self.config_dict = config_dict

        if set(self.config_dict) != set(self.tools_by_criterion_dict):
            logging.error("mismatch between tools and config"}
            ERROR_HANDLER.error_exit()
        for criterion in self.config_dict:
            if len(self.tools_by_criterion_dict[criterion]) != \
                            len(set(self.tools_by_criterion_dict[criterion])):
                logging.error("{} {}".format( \
                            "some tools appear multiple times for criterion", \
                            criterion)
                ERROR_HANDLER.error_exit()
            if len(self.config_dict[criterion]) != \
                                len(self.tools_by_criterion_dict[criterion]):
                logging.error("{} {} {}".format("mismatch in number of tools", \
                        "between config and tools_by_criterion for criterion", \
                                                                    criterion))
                ERROR_HANDLER.error_exit()

        if self.codecoverage_working_dir is not None:
            if not os.path.isdir(self.codecoverage_working_dir):
                os.mkdir(self.codecoverage_working_dir)
        else:
            logging.error("Must specify codecoverage_working_dir")
            ERROR_HANDLER.error_exit()

        self.checkpoints_dir = os.path.join(self.codecoverage_working_dir, \
                                                                "_checkpoints_")
        if not os.path.isdir(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)

        self.checkpointer = common_fs.CheckpointState(\
                                                *self.get_checkpoint_files())

        self.codecoverage_tool_handle = {}
        for criterion in self.tools_by_criterion_dict:
            for toolname in self.tools_by_criterion_dict[criterion]:
                config = config_dict[criterion]
                if toolname in self.codecoverage_tool_handle:
                    self.codecoverage_tool_handle\
                            [self.TOOL_OBJ_KEY]['config'] = \
                                    self.codecoverage_tool_handle\
                                [self.TOOL_OBJ_KEY]['config'].mergewith(config)
                else:
                    tool_working_dir = self.get_codecoverage_tool_out_folder( \
                                                                    toolname)
                    tool_checkpointer = common_fs.CheckpointState( \
                            *self.get_mutation_tool_checkpoint_files(toolname))
                    self.checkpointer.add_dep_checkpoint_state( \
                                                            tool_checkpointer)
                    self.codecoverage_tool_handle[toolname] = {
                        'language': language, 'toolname': toolname, 
                        'tool_working_dir': tool_working_dir, 'config': config, 
                        'tool_checkpointer': tool_checkpointer
                    }

        # create the tools
        for toolname in self.codecoverage_tool_handle:
            self.codecoverage_tool_handle[toolname] = {
                self.TOOL_OBJ_KEY: self.get_codecoverage_tool(\
                                    **self.codecoverage_tool_handle[toolname]),
                self.TOOL_WORKDIR_KEY: self.codecoverage_tool_handle\
                                                [toolname]['tool_working_dir'],
            }

        # verify supported criteria
        for criterion in self.tools_by_criterion_dict:
            for toolname in self.tools_by_criterion_dict[criterion]:
                if criterion not in self.codecoverage_tool_handle[toolname].\
                                                    get_supported_criteria():
                    logging.error(\
                            "tool {} specified for unsupported criterion {}".\
                                                format(toolname, criterion))
                    ERROR_HANDLER.error_exit()
    #~ def __init__()

    def get_codecoverage_tool(self, language, toolname, tool_working_dir, \
                                                    config, tool_checkpointer):
        '''
            Each tool module must have the function createCodecoverageTool() 
            implemented
        '''
        ccov_tool = self.modules_dict[language][toolname].CodecoverageTool(
                                            self.meta_test_generation_obj,
                                            tool_working_dir,
                                            self.code_builder,
                                            config,
                                            tool_checkpointer)
        return ccov_tool
    #~ def get_codecoverage_tool()

    def get_tool2criteria_values(criteria_passed_values)
        '''
        Take values by criteria and return values by tools. This map the
        criteria to the correspondng tools to have each tool linked to its
        representing criteria which are further linked to the object values.

        :param criteria_passed_values: dict representing a certain object value
                by criterion (value for each criterion)
        :return: return the object values by tools
        '''
        none_activated_default = {c: None for c in self.CRITERIA_LIST}
        tool2criteria_values = {}
        for criterion in criteria_passed_values:
            for ctoolname in self.tools_by_criterion_dict[criterion]:
                if ctoolname not in tool2criteria_values:
                    tool2criteria_values[ctoolname] = \
                                                none_activated_default.copy()
                tool2criteria_values[ctoolname][criterion] = \
                                            criteria_passed_values[criterion]
        return tool2criteria_values
    #~ def get_tool2criteria_values()
                                            
    def runtests_code_coverage (self, testcases, re_instrument_code=True, \
                                            statement_matrix=None, \
                                            branch_matrix=None, \
                                            function_matrix=None):
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
        '''

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "runtests_code_coverage"
        cp_task_id = 1
        checkpoint_handler = CheckpointHandlerForMeta(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        assert statement_matrix is not None or branch_matrix is not None \
                    or function_matrix is not None, "no criterion is enabled"
        criteria_passed_values = {}
        criteria_passed_values[self.STATEMENT_KEY] = statement_matrix
        criteria_passed_values[self.BRANCH_KEY] = branch_matrix
        criteria_passed_values[self.FUNCTION_KEY] = function_matrix

        assert len(set(criteria_passed_values) - \
                    set(self.tools_by_criterion_dict)) = 0, \
                        "Passed matrices output are more than tool specified"

        tool2criteria_values = get_tool2criteria_values(criteria_passed_values)

        for ctoolname in tool2criteria_values:
            # Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolname)

                # Actual execution
                ctool = self.codecoverage_tool_handle[ctoolname][\
                                                            self.TOOL_OBJ_KEY]
                ctool.runtests_code_coverage(testcases, \
                        criterion_to_matrix = tool2criteria_values[ctoolname], \
                        re_instrument_code=re_instrument_code)

                # Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolname)

        # @Checkpoint: Finished
        detailed_exectime = {ct: ct.get_checkpointer().get_execution_time() \
                                                for ct in tool2criteria_values}
        checkpoint_handler.set_finished(detailed_exectime_obj=detailed_exectime)
    #~ def runtests_code_coverage()

    def instrument_code (self, outputdir=None, code_builder_override=None,
                                statement_enabled=self.STATEMENT_DEFAULT,
                                branch_enabled=self.BRANCH_DEFAULT,
                                function_enabled=self.FUNCTION_DEFAULT):
        '''
        '''
        # @Checkpoint: create a checkpoint handler
        cp_func_name = "instrument_code"
        cp_task_id = 1
        checkpoint_handler = CheckpointHandlerForMeta(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        assert statement_enabled or branch_enabled or function_enabled, \
                                                    "no criterion is enabled"

        criteria_passed_values = {}
        criteria_passed_values[self.STATEMENT_KEY] = statement_enabled
        criteria_passed_values[self.BRANCH_KEY] = branch_enabled
        criteria_passed_values[self.FUNCTION_KEY] = function_enabled

        assert len(set(criteria_passed_values) \
                    - set(self.tools_by_criterion_dict)) = 0, \
                        "Passed matrice output are more than toll specified"

        tool2criteria_values = get_tool2criteria_values(criteria_passed_values)

        for ctoolname in tool2criteria_values:
            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolname)
                # Actual execution
                ctool = self.codecoverage_tool_handle[ctoolname][\
                                                            self.TOOL_OBJ_KEY]
                ctool.instrument_code(outputdir, code_builder_override, \
                        criterion_to_enabling = tool2criteria_values[ctoolname])

                # @Checkpoint: Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=ctoolname)

        # @Checkpoint: Finished
        detailed_exectime = {ct: ct.get_checkpointer().get_execution_time() \
                                                for ct in tool2criteria_values}
        checkpoint_handler.set_finished(detailed_exectime_obj=detailed_exectime)
    #~ def instrument_code()

    def get_codecoverage_tool_out_folder(ccov_toolname, top_outdir=None):
        if top_outdir is None:
            top_outdir = self.codecoverage_working_dir
        return os.path.join(top_outdir, ccov_toolname)
    #~def get_codecoverage_tool_out_folder()

    def get_codecoverage_tool_checkpoint_files(self, codecoverage_toolname, \
                                                    top_checkpoint_dir=None):
        if top_checkpoint_dir is None:
            top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                        codecoverage_toolname+"_checkpoint.state"+suffix) \
                        for suffix in ("", ".backup")]
    #~def get_codecoverage_tool_checkpoint_files()
        
    def get_checkpoint_files(self):
        top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                        "checkpoint.state"+suffix) \
                        for suffix in ("", ".backup")]
    #~def get_checkpoint_files()

    def get_checkpointer(self):
        return self.checkpointer
    #~ def get_checkpointer()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer()
#~ class MetaCodecoverageTool
