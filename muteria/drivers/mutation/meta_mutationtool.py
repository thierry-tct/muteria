
# This module is used through MetaMutationTool class
# Which access the relevant mutation tools as specified

# The tools are organized by programming language
# For each language, there is a folder for each tool, 
# named after the tool in lowercase

# Each mutation tool package have the following in the __init__.py file:
# import <Module>.<class extending BaseMutationTool> as MutationTool

from __future__ import print_function
import os
import sys
import glob
import copy
import logging

import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from base_mutationtool import BaseMutationTool

from ... import ToolsModulesLoader

from ...checkpoint_handler import CheckpointHandlerForMeta

ERROR_HANDLER = common_mix.ErrorHandler()

class MetaMutationTool(object):
    ''' 
    '''

    TOOL_OBJ_KEY = "tool_obj"
    TOOL_WORKDIR_KEY = "tool_working_dir"

    def __init__(self, meta_test_generation_obj,
                        mutation_working_dir,
                        code_builder,
                        language, 
                        mutation_toolname_list, 
                        config_list):
        self.modules_dict = ToolsModulesLoader.get_tools_modules(
                                    ToolsModulesLoader.MUTATION_TOOLS)
        if len(mutation_toolname_list) != len(config_list):
            logging.error("mismatch between number of toolnames and configs")
            ERROR_HANDLER.error_exit()
        if len(mutation_toolname_list) != len(set(mutation_toolname_list)):
            logging.error("some tools appear multiple times.")
            ERROR_HANDLER.error_exit()

        self.meta_test_generation_obj = meta_test_generation_obj
        self.mutation_working_dir = mutation_working_dir
        self.code_builder = code_builder

        if self.mutation_working_dir is not None:
            if not os.path.isdir(self.mutation_working_dir):
                os.mkdir(self.mutation_working_dir)
        else:
            logging.error("Must specify mutation_working_dir")
            ERROR_HANDLER.error_exit()

        self.checkpoints_dir = os.path.join(self.mutation_working_dir, \
                                                            "_checkpoints_")
        if not os.path.isdir(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)

        self.checkpointer = common_fs.CheckpointState( \
                                                *self.get_checkpoint_files())
        
        #self.mutant_id_mapping_jsonfile = \
        #    os.path.join(self.mutation_working_dir, "mutant_id_mapping.json")

        self.mutant_info_file = \
            os.path.join(self.mutation_working_dir, "mutant_info_file.json")

        self.mutation_tools = {}
        for idx in range(len(mutation_toolname_list)):
            toolname = mutation_toolname_list[idx]
            tool_working_dir = self.get_mutation_tool_out_folder(toolname)
            config = config_list[idx]
            tool_checkpointer = common_fs.CheckpointState( \
                            *self.get_mutation_tool_checkpoint_files(toolname))
            self.checkpointer.add_dep_checkpoint_state(tool_checkpointer)
            self.mutation_tools[toolname] = {
                self.TOOL_OBJ_KEY: self.get_mutation_tool(language, toolname, \
                                                tool_working_dir, config, \
                                                tool_checkpointer),
                self.TOOL_WORKDIR_KEY: tool_working_dir,
            }
    #~ def __init__()

    def get_mutation_tool(self, language, toolname, tool_working_dir, config, tool_checkpointer):
        '''
            Each tool module must have the function createMutationTool() implemented
        '''
        mutation_tool = self.modules_dict[language][toolname].MutationTool(
                                            self.meta_test_generation_obj,
                                            tool_working_dir,
                                            self.code_builder,
                                            config,
                                            tool_checkpointer)
        return mutation_tool
    #~ def get_mutation_tool()

    def runtest_generic (self, testcases, result_matrix, meta_mutantlist, \
                                                mode, serialize_period=1, \
                                                strong_kill_only_once=False):
        # @Checkpoint: create a checkpoint handler
        cp_func_name = "runtest_generic:"+mode
        cp_task_id = 1
        checkpoint_handler = CheckpointHandlerForMeta(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        matrices_dir_tmp = os.path.join(self.mutation_working_dir, \
                                                            mode+"_dir.tmp")
        if os.path.isdir(matrices_dir_tmp):
            shutil.rmtree(matrices_dir_tmp)
        os.mkdir(matrices_dir_tmp)

        mutantlist_by_tool = {}
        for meta_mutant in meta_mutantlist:
            mtoolname, mutant = self.reverse_meta_key(meta_mutant)
            if mtoolname not in mutantlist_by_tool:
                mutantlist_by_tool[mtoolname] = []
            mutantlist_by_tool[mtoolname].append(mutant)

        assert len(set(mutantlist_by_tool) - set(self.mutation_tools)) == 0, \
                                                "tool in data not registered"
        matrix_files_map = {}
        for mtoolname in mutantlist_by_tool:
            # @Checkpoint: Check whether already executed
            if not checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=mtoolname)
                continue

            matrix_files_map[mtoolname] = os.path.join(\
                                            matrices_dir_tmp, mtoolname+'.csv')
            tool_matrix = result_matrix.get_a_deepcopy(\
                                    new_filename=matrix_files_map[mtoolname])
            mut_tool = self.mutation_tools[mtoolname][self.TOOL_OBJ_KEY]
            if mode == "mutant_coverage":
                mut_tool.runtest_mutant_coverage(testcases, tool_matrix, \
                                                mutantlist_by_tool[mtoolname])
            elif mode == "weak_mutation":
                mut_tool.runtest_weak_mutation(testcases, tool_matrix, \
                                                mutantlist_by_tool[mtoolname])
            elif mode == "strong_mutation":
                mut_tool.runtest_strong_mutation(testcases, tool_matrix, \
                            mutantlist_by_tool[mtoolname], serialize_period, \
                                                        strong_kill_only_once)
            else:
                logging("Invalid mode: {}".format(mode))
                ERROR_HANDLER.error_exit()
            
            # @Checkpoint: Checkpointing
            checkpoint_handler.do_checkpoint( \
                                    func_name=cp_func_name, \
                                    taskid=cp_task_id, \
                                    tool=mtoolname)

        # Aggregate the matrices
        for mtoolname in matrix_files_map:
            tool_matrix = common_matrices.ExecutionMatrix(\
                                        filename=matrix_files_map[mtoolname])

            # Check columns
            assert tool_matrix.get_key_colname() == \
                                        result_matrix.get_key_colname(), \
                                              "mismatch on key column name"
            assert set(tool_matrix.get_nonkey_colname_list()) == \
                            set(result_matrix.get_nonkey_colname_list()), \
                                            "mismatch on non key column names"

            # bring in the data
            key2nonkeydict = tool_matrix.get_pandas_df().\
                            set_index(tool_matrix.get_key_colname, drop=True).\
                                            to_dict(orient="index")
            for m_key in key2nonkeydict:
                meta_m_key = self.get_meta_key(m_key, mtoolname)
                result_matrix.add_row_by_key(meta_m_key, 
                                                    key2nonkeydict[m_key], 
                                                    serialize=False)

        # Serialized the computed matrix
        result_matrix.serialize()
        
        # Delete the temporary tool matrix's directory
        shutil.rmtree(matrices_dir_tmp)

        # @Checkpoint: Finished
        detailed_exectime = {mt: mt.get_checkpointer().get_execution_time() \
                                            for mt in self.mutantlist_by_tool}
        checkpoint_handler.set_finished(detailed_exectime_obj=detailed_exectime)
    #~ runtest_generic()

    def runtest_mutant_coverage (self, testcases, mutant_coverage_matrix, \
                                                                    mutantlist):
        self.runtest_generic (testcases, mutant_coverage_matrix, mutantlist, \
                                                            "mutant_coverage")
    #~ def runtest_mutant_coverage()
        
    def runtest_weak_mutation (self, testcases, weak_mutation_matrix, \
                                                                    mutantlist):
        self.runtest_generic (testcases, weak_mutation_matrix, mutantlist, \
                                                                "weak_mutation")
    #~ runtest_weak_mutation()

    def runtest_strong_mutation (self, testcases, strong_mutation_matrix,
                                     mutantlist, serialize_period=1):
        self.runtest_generic (testcases, strong_mutation_matrix, mutantlist, 
                                "strong_mutation",
                                serialize_period=serialize_period, 
                                strong_kill_only_once=strong_kill_only_once)
    #~ def runtest_strong_mutation()

    def mutate_programs (self):
        # @Checkpoint: create a checkpoint handler
        cp_func_name = "mutate_programs"
        cp_task_id = 1
        checkpoint_handler = CheckpointHandlerForMeta(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        # Mutate
        for mtoolname in self.mutation_tools:
            # @Checkpoint: Check whether already executed
            if checkpoint_handler.is_to_execute( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=mtoolname)

                # Actual Execution
                mut_tool = self.mutation_tools[mtoolname][self.TOOL_OBJ_KEY]
                mut_tool.mutate_programs()

                # @Checkpoint: Checkpointing
                checkpoint_handler.do_checkpoint( \
                                        func_name=cp_func_name, \
                                        taskid=cp_task_id, \
                                        tool=mtoolname)

        # Compute mutant info
        meta_mutant_info_obj = {}
        for mtoolname in self.mutation_tools:
            mut_tool = self.mutation_tools[mtoolname][self.TOOL_OBJ_KEY]
            tool_mutant_info = mut_tool.get_mutant_info_object()
            for m_key in tool_mutant_info:
                meta_m_key = self.get_meta_key(m_key, mtoolname)
                assert meta_m_key not in meta_mutant_info_obj, \
                                                "Key already existing (BUG)"
                meta_mutant_info_obj[meta_m_key] = tool_mutant_info[m_key]
        self.store_mutant_info_to_file(meta_mutant_info_obj)

        # @Checkpoint: Finished
        detailed_exectime = {mt: mt.get_checkpointer().get_execution_time() \
                                                for mt in self.mutation_tools}
        checkpoint_handler.set_finished(detailed_exectime_obj=detailed_exectime)
    #~ def mutate_programs()
    
    def get_meta_key(key, toolname):
        return ":".join([toolname, key])
    #~ def get_meta_key()

    def reverse_meta_key(meta_key, toolname):
        parts = meta_key.split(':', 1)
        assert len(parts) >= 2, "invalibd meta key"
        toolname, key = parts
        return toolname, key
    #~ def reverse_meta_key()

    def get_mutant_info_object(self):
        return common_fs.loadJSON(self.get_mutant_info_file())
    #~ def def get_mutant_info_object()

    def store_mutant_info_to_file(self, data_object):
        common_fs.dumpJSON(data_object, self.get_mutant_info_file())
    #~ def store_mutant_info_to_file()

    def get_mutant_info_file(self):
        return self.mutant_info_file
    #~ def get_mutant_info_file()

    def get_mutation_tool_out_folder(self, mutation_toolname, top_outdir=None):
        if top_outdir is None:
            top_outdir = self.mutation_working_dir
        return os.path.join(top_outdir, mutation_toolname)
    #~ def get_mutation_tool_out_folder()

    def get_mutation_tool_checkpoint_files(self, mutation_toolname, \
                                                    top_checkpoint_dir=None):
        if top_checkpoint_dir is None:
            top_checkpoint_dir = self.checkpoints_dir
        return [os.path.join(top_checkpoint_dir, \
                            mutation_toolname+"_checkpoint.state"+suffix) \
                            for suffix in ("", ".backup")]
    #~ def get_mutation_tool_checkpoint_files()
        
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
    #~ def has_checkpointer()

    #def getMutantIDMappingJsonFile(self):
    #    return self.mutant_id_mapping_jsonfile

    #def loadMutantIDMappingJsonFile(self):
    #    return common_fs.loadJSON(self.getMutantIDMappingJsonFile())
        
    #def storeMutantIDMappingJsonFile(self, data_object):
    #    common_fs.dumpJSON(data_object, self.getMutantIDMappingJsonFile())
#~ class MetaMutationTool 
