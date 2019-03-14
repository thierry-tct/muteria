#
# [LICENCE]
#
"""
This module is used through MetaMutationTool class
Which access the relevant mutation tools as specified

The tools are organized by programming language
For each language, there is a folder for each tool, 
named after the tool in lowercase

Each mutation tool package have the following in the __init__.py file:
>>> import <Module>.<class extending BaseMutationTool> as MutationTool
"""

from __future__ import print_function
import os
import sys
import glob
import copy
import shutil
import logging

import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from muteria.drivers import ToolsModulesLoader
from muteria.drivers import DriversUtils

from muteria.drivers.checkpoint_handler import CheckPointHandler

from muteria.drivers.mutation.mutants_info import MutantsInfoObject

ERROR_HANDLER = common_mix.ErrorHandler

class MetaMutationTool(object):
    ''' 
    '''

    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"

    def __init__(self, language, meta_test_generation_obj,
                        mutation_working_dir,
                        code_builds_factory,
                        mutation_tool_config_list):
        # Set Constants
        self.modules_dict = ToolsModulesLoader.get_tools_modules(
                                    ToolsModulesLoader.MUTATION_TOOLS)

        # Set Direct Arguments Variables
        self.language = language
        self.meta_test_generation_obj = meta_test_generation_obj
        self.mutation_working_dir = mutation_working_dir
        self.code_builds_factory = code_builds_factory
        self.mutation_tool_config_list = mutation_tool_config_list
        
        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.mutation_working_dir is None, \
                                "Must specify mutation_working_dir", __file__)
        ERROR_HANDLER.assert_true(len(self.mutation_tool_config_list) != \
                                len(set([c.get_tool_config_alias() for c in \
                                        self.mutation_tool_config_list])), \
                        "some tool configs appear multiple times", __file__)
        
        # Set Indirect Arguments Variables
        self.checkpoints_dir = os.path.join(self.mutation_working_dir, \
                                                            "_checkpoints_")
        self.mutants_info_file = \
            os.path.join(self.mutation_working_dir, "mutants_info_file.json")
        
        # Verify indirect Arguments Variables
        
        # Initialize Other Fields
        self.mutation_configured_tools = {}
        self.checkpointer = None
        
        # Make Initialization Computation
        ## Create dirs
        if not os.path.isdir(self.mutation_working_dir):
            os.mkdir(self.mutation_working_dir)

        if not os.path.isdir(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)

        ## Set checkpointer
        self.checkpointer = common_fs.CheckpointState( \
                                                *self._get_checkpoint_files())
        
        ## Create the different tools
        for idx in range(len(self.mutation_tool_config_list)):
            config = self.mutation_tool_config_list[idx]
            toolname = config.get_tool_name()
            toolalias = config.get_tool_config_alias()
            tool_working_dir = self._get_mutation_tool_out_folder(toolalias)
            tool_checkpointer = common_fs.CheckpointState( \
                            *self._get_mutation_tool_checkpoint_files(toolalias))
            self.checkpointer.add_dep_checkpoint_state(tool_checkpointer)
            self.mutation_configured_tools[toolalias] = {
                self.TOOL_OBJ_KEY: self._create_mutation_tool(toolname, \
                                                tool_working_dir, config, \
                                                tool_checkpointer),
                self.TOOL_WORKDIR_KEY: tool_working_dir,
            }
    #~ def __init__()

    def _create_mutation_tool(self, toolname, tool_working_dir, \
                                                    config, tool_checkpointer):
        '''
            
        '''
        ERROR_HANDLER.assert_true( \
            toolname in self.modules_dict[self.language],
            "Invalid toolname given: {}".format(toolname), __file__)
        try:
            # the tooltype is returned by config.get_tool_type()
            MutationTool = getattr(self.modules_dict[self.language][toolname],\
                                    config.get_tool_type().get_field_value())
        except AttributeError:
            ERROR_HANDLER.error_exit("{} {} {} {}".format( \
                                "(REPORT BUG) The mutation tool of type", \
                                config.get_tool_type().get_field_value(),\
                                "is not present for test tool", toolname), \
                                                                    __file__)

        ERROR_HANDLER.assert_true(MutationTool is not None, \
                                "The {} language's tool {} {} {}.".format( \
                                self.language, toolname, \
                                "does not implement the mutation tool type", \
                                config.get_tool_type().get_str()), __file__)
        mutation_tool = MutationTool(self.meta_test_generation_obj, \
                                        tool_working_dir, \
                                        self.code_builds_factory, \
                                            config, tool_checkpointer)
        return mutation_tool
    #~ def _create_mutation_tool()

    def _runtest_generic (self, testcases, result_matrix, meta_mutantlist, \
                                        mode, serialize_period=1, \
                                        strong_kill_only_once=False,
                                        mutant_prioritization_module=None, \
                                        parallel_count=1, \
                                        parallel_mutant_test_scheduler=None, \
                                        restart_checkpointer=False,
                                        finish_destroy_checkpointer=True):
        """ Description
        :type self:
        :param self:

        :type testcases:
        :param testcases:

        :type result_matrix:
        :param result_matrix: Must be an empty matrix

        :type meta_mutantlist:
        :param meta_mutantlist:

        :type \mode:
        :param \mode:

        :type serialize_period:
        :param serialize_period:

        :type \strong_kill_only_once:
        :param \strong_kill_only_once:

        :type mutant_prioritization_module:
        :param mutant_prioritization_module:
                        (TODO: Implement support)

        :type \parallel_count:
        :param \parallel_count:

        :type \parallel_mutant_test_scheduler:
        :param \parallel_mutant_test_scheduler:
                        (TODO: Implement support)

        :type \restart_checkpointer:
        :param \restart_checkpointer:

        :type finish_destroy_checkpointer:
        :param finish_destroy_checkpointer:

        :raises:

        :rtype:
        """

        # FIXME: Make sure that the support are implemented for 
        # parallelism and test prioritization. Remove the code bellow 
        # once supported:
        ERROR_HANDLER.assert_true(mutant_prioritization_module is None, \
                        "Must implement mutant prioritization support here", \
                                                                    __file__)
        ERROR_HANDLER.assert_true(parallel_count <= 1, \
                    "Must implement parallel execution support here", \
                                                                    __file__)
        ERROR_HANDLER.assert_true(parallel_mutant_test_scheduler is None, \
            "Must implement parallel mutant tests execution support here", \
                                                                    __file__)
        #~FIXMEnd

        # Check arguments Validity
        ERROR_HANDLER.assert_true(parallel_count > 0, \
                    "invalid parallel  execution count: {}. {}".format( \
                                    parallel_count, "must be >= 1"), __file__)

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "_runtest_generic:"+mode
        cp_task_id = 1
        checkpoint_handler = CheckPointHandler( \
                                            self.get_checkpoint_state_object())
        if restart_checkpointer:
            checkpoint_handler.restart()
        if checkpoint_handler.is_finished():
            return

        matrices_dir_tmp = os.path.join(self.mutation_working_dir, \
                                                            mode+"_dir.tmp")
        if os.path.isdir(matrices_dir_tmp):
            if restart_checkpointer:
                shutil.rmtree(matrices_dir_tmp)
                os.mkdir(matrices_dir_tmp)
        else:
            os.mkdir(matrices_dir_tmp)

        mutantlist_by_tool = {}
        for meta_mutant in meta_mutantlist:
            mtoolalias, mutant = DriversUtils.reverse_meta_element(meta_mutant)
            if mtoolalias not in mutantlist_by_tool:
                mutantlist_by_tool[mtoolalias] = []
            mutantlist_by_tool[mtoolalias].append(mutant)

        ERROR_HANDLER.assert_true(len(set(mutantlist_by_tool) - \
                                set(self.mutation_configured_tools)) == 0, \
                                    "tool in data not registered", __file__)
        matrix_files_map = {}
        for mtoolalias in mutantlist_by_tool:
            matrix_files_map[mtoolalias] = os.path.join(matrices_dir_tmp, \
                                                            mtoolalias+'.csv')

            # @Checkpoint: Check whether already executed
            if not checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=mtoolalias):
                continue

            tool_matrix = result_matrix.get_a_deepcopy(\
                                    new_filename=matrix_files_map[mtoolalias])
            mut_tool = self.mutation_configured_tools[mtoolalias]\
                                                            [self.TOOL_OBJ_KEY]
            if mode == "mutant_coverage":
                mut_tool.runtest_mutant_coverage(testcases, tool_matrix, \
                                                mutantlist_by_tool[mtoolalias])
            elif mode == "weak_mutation":
                mut_tool.runtest_weak_mutation(testcases, tool_matrix, \
                                                mutantlist_by_tool[mtoolalias])
            elif mode == "strong_mutation":
                mut_tool.runtest_strong_mutation(testcases, tool_matrix, \
                            mutantlist_by_tool[mtoolalias], serialize_period, \
                            strong_kill_only_once, \
                            mutant_prioritization_module.\
                                    get_mutant_test_run_optimizer(mtoolalias))
            else:
                ERROR_HANDLER.error_exit("Invalid mode: {}".format(mode))
            
            # @Checkpoint: Checkpointing
            checkpoint_handler.do_checkpoint( \
                                    func_name=cp_func_name, \
                                    taskid=cp_task_id, \
                                    tool=mtoolalias)

        # Aggregate the matrices
        for mtoolalias in matrix_files_map:
            tool_matrix = common_matrices.ExecutionMatrix(\
                                        filename=matrix_files_map[mtoolalias])

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
            for m_key in key2nonkeydict:
                meta_m_key = DriversUtils.make_meta_element(m_key, mtoolalias)
                result_matrix.add_row_by_key(meta_m_key, 
                                                    key2nonkeydict[m_key], 
                                                    serialize=False)

        # @Checkpoint: Next task id (serialize)
        cp_task_id += 1
        # @Checkpoint: Check whether already executed
        if checkpoint_handler.is_to_execute( \
                                    func_name=cp_func_name, \
                                    taskid=cp_task_id):
            # Serialized the computed matrix
            result_matrix.serialize()
        # @Checkpoint: Checkpointing
        checkpoint_handler.do_checkpoint( \
                                func_name=cp_func_name, \
                                taskid=cp_task_id)
        
        # Delete the temporary tool matrix's directory
        if os.path.isdir(matrices_dir_tmp):
            shutil.rmtree(matrices_dir_tmp)

        # @Checkpoint: Finished
        detail_exectime = {mt: mt.get_checkpointer().get_execution_time() \
                                            for mt in mutantlist_by_tool}
        checkpoint_handler.set_finished(detailed_exectime_obj=detail_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()
    #~ _runtest_generic()

    def runtest_mutant_coverage (self, testcases, mutant_coverage_matrix_file,\
                                                                mutantlist, \
                                                            parallel_count=1, \
                                                restart_checkpointer=False, \
                                            finish_destroy_checkpointer=True):

        # Load or Create the matrix 
        mutant_coverage_matrix = common_matrices.ExecutionMatrix( \
                                        filename=mutant_coverage_matrix_file, \
                                                    non_key_col_list=testcases)
        ERROR_HANDLER.assert_true(mutant_coverage_matrix.is_empty(), \
                                        "matrix must be empty", __file__)
        self._runtest_generic (testcases, mutant_coverage_matrix, mutantlist, \
                                                        "mutant_coverage", \
                                            parallel_count=parallel_count, \
                                restart_checkpointer=restart_checkpointer, \
                    finish_destroy_checkpointer=finish_destroy_checkpointer)
    #~ def runtest_mutant_coverage()
        
    def runtest_weak_mutation (self, testcases, weak_mutation_matrix_file, \
                                                                mutantlist, \
                                                    parallel_count=1, \
                                                restart_checkpointer=False, \
                                            finish_destroy_checkpointer=True):

        # Load or Create the matrix 
        weak_mutation_matrix = common_matrices.ExecutionMatrix( \
                                        filename=weak_mutation_matrix_file, \
                                                    non_key_col_list=testcases)
        ERROR_HANDLER.assert_true(weak_mutation_matrix.is_empty(), \
                                        "matrix must be empty", __file__)
        self._runtest_generic (testcases, weak_mutation_matrix, mutantlist, \
                                                            "weak_mutation",
                                            parallel_count=parallel_count, \
                                restart_checkpointer=restart_checkpointer, \
                    finish_destroy_checkpointer=finish_destroy_checkpointer)
    #~ runtest_weak_mutation()

    def runtest_strong_mutation (self, testcases, strong_mutation_matrix_file,\
                                            mutantlist, serialize_period=1, \
                                                strong_kill_only_once=False, \
                                        mutant_prioritization_module=None, \
                                        parallel_count=1, \
                                        parallel_mutant_test_scheduler=None, \
                                        restart_checkpointer=False,
                                        finish_destroy_checkpointer=True):

        # Load or Create the matrix 
        strong_mutation_matrix = common_matrices.ExecutionMatrix( \
                                        filename=strong_mutation_matrix_file, \
                                                    non_key_col_list=testcases)
        ERROR_HANDLER.assert_true(strong_mutation_matrix.is_empty(), \
                                        "matrix must be empty", __file__)
        self._runtest_generic (testcases, strong_mutation_matrix, mutantlist, 
                                "strong_mutation",
                                serialize_period=serialize_period, 
                                strong_kill_only_once=strong_kill_only_once,
                mutant_prioritization_module=mutant_prioritization_module, \
                                        parallel_count=parallel_count, \
                parallel_mutant_test_scheduler=parallel_mutant_test_scheduler,\
                                    restart_checkpointer=restart_checkpointer,
                    finish_destroy_checkpointer=finish_destroy_checkpointer)
    #~ def runtest_strong_mutation()

    def mutate_programs (self, exe_path_map,
                                parallel_mutation_count=1, \
                                restart_checkpointer=False,
                                finish_destroy_checkpointer=True):
        # FIXME: Support parallelism, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(parallel_mutation_count <= 1, \
                "FIXME: Must first implement support for parallel mutation")
        #~ FXIMEnd

        # Check arguments Validity
        ERROR_HANDLER.assert_true(parallel_mutation_count > 0, \
                    "invalid parallel  execution count: {}. {}".format( \
                            parallel_mutation_count, "must be >= 1"), __file__)

        # @Checkpoint: create a checkpoint handler
        cp_func_name = "mutate_programs"
        cp_task_id = 1
        checkpoint_handler = CheckPointHandler( \
                                            self.get_checkpoint_state_object())
        if restart_checkpointer:
            checkpoint_handler.restart()
        if checkpoint_handler.is_finished():
            return

        candidate_tools_alias = self.mutation_configured_tools.keys()

        # Mutate
        for mtoolalias in candidate_tools_alias:
            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=mtoolalias):

                # Actual Execution
                mut_tool = self.mutation_configured_tools[mtoolalias]\
                                                            [self.TOOL_OBJ_KEY]
                mut_tool.mutate_programs()

                # @Checkpoint: Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=mtoolalias)

        # Invalidate any existing mutant info so it can be recomputed
        self._invalidate_mutant_info()

        # @Checkpoint: Finished
        detail_exectime = {mt: mt.get_checkpointer().get_execution_time() \
                                    for mt in self.mutation_configured_tools}
        checkpoint_handler.set_finished(detailed_exectime_obj=detail_exectime)

        if finish_destroy_checkpointer:
            checkpoint_handler.destroy()
    #~ def mutate_programs()

    def _compute_mutants_info(self, candidate_tool_aliases=None):
        meta_mutant_info_obj = MutantsInfoObject()
        if candidate_tool_aliases is None:
            candidate_tool_aliases = self.mutation_configured_tools.keys()
        for mtoolalias in candidate_tool_aliases:
            ttool = \
                self.mutation_configured_tools[mtoolalias][self.TOOL_OBJ_KEY]
            tool_mutant_info = ttool.get_mutant_info_object()
            old2new_tests = {}
            for m_test in tool_mutant_info.get_tests_list():
                meta_t_key = DriversUtils.make_meta_element(m_test, mtoolalias)
                old2new_tests[m_test] = meta_t_key
            meta_mutant_info_obj.update_using(mtoolalias, old2new_tests, \
                                                            tool_mutant_info)
        return meta_mutant_info_obj
    #~ def _compute_mutants_info()
    
    def get_mutant_info_object(self):
        return MutantsInfoObject().load_from_file(\
                                                self.get_mutant_info_file())
    #~ def def get_mutant_info_object()

    def get_mutant_info_file(self):
        # Compute and write the testcase info if not present
        # only place where the meta info is written
        if self._mutant_info_is_invalidated():
            self._compute_mutants_info().write_to_file(\
                                        self._unchecked_get_mutant_info_file())
        return self._unchecked_get_mutant_info_file()
    #~ def get_mutant_info_file()

    def _unchecked_get_mutant_info_file(self):
        return self.mutants_info_file
    #~ def _unchecked_get_mutant_info_file():

    def _invalidate_mutant_info(self):
        if os.path.isfile(self._unchecked_get_mutant_info_file()):
            os.remove(self._unchecked_get_mutant_info_file())
    #~ def _invalidate_mutant_info()

    def _mutant_info_is_invalidated(self):
        return not os.path.isfile(self._unchecked_get_mutant_info_file())
    #~ def _mutant_info_is_invalidated()

    def _get_mutation_tool_out_folder(self, mutation_toolname, top_outdir=None):
        if top_outdir is None:
            top_outdir = self.mutation_working_dir
        return os.path.join(top_outdir, mutation_toolname)
    #~ def _get_mutation_tool_out_folder()

    def _get_mutation_tool_checkpoint_files(self, mutation_toolalias, \
                                                    top_checkpoint_dir=None):
        if top_checkpoint_dir is None:
            top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                            mutation_toolalias+"_checkpoint.state"+suffix) \
                            for suffix in ("", ".backup")]
    #~ def _get_mutation_tool_checkpoint_files()
        
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
    #~ def has_checkpointer()