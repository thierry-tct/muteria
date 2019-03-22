"""
TODO: Add support for multi versions of results 
"""

from __future__ import print_function

import os 
import logging
import shutil
import glob

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

import muteria.controller.explorer as outdir_struct
import muteria.controller.logging_setup as logging_setup
from muteria.repositoryandcode.repository_manager import RepositoryManager
from muteria.repositoryandcode.code_builds_factory import CodeBuildsFactory

ERROR_HANDLER = common_mix.ErrorHandler

class Executor(object):
    TASK_KEY = "tasks_key"
    TEST_TOOL_TYPES_KEY = "test_tool_types_key"
    def __init__(self, config, top_timeline_explorer):
        self.config = config
        self.top_timeline_explorer = top_timeline_explorer

        self.head_explorer = self.top_timeline_explorer.get_latest_explorer()
        self._initialize_output_structure(cleanstart=\
                                self.config.EXECUTION_CLEANSTART._get_val())
        if not logging_setup.is_setup():
            logging_setup.setup(logfile=self.head_explorer.get_file_pathname(\
                                                outdir_struct.MAIN_LOG_FILE))
        # Create repo manager
        # XXX The repo manager automatically revert any previous problem
        self.repo_mgr = self._create_repo_manager(config)

        # set error handlers for revert repo
        common_mix.ErrorHandler.set_corresponding_repos_manager(self.repo_mgr)

        # create codes builders
        self.cb_factory = CodeBuildsFactory(self.repo_mgr)
    #~ def __init__()

    def main(self):
        """ Executor entry point
        """
        # Initialize output structure
        self._initialize_output_structure(cleanstart=self.config.CLEANSTART)

        # Make checkpointer
        checkpointer = common_fs.CheckpointState(*self._get_checkpoint_files())

        # See whether starting or continuing

    #~ def main()

    def _create_repo_manager(self, config):
        # TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
        repo_mgr = None #TODO
        return repo_mgr
    #~ def __create_repo_manager()

    def _create_meta_test_tool(self):
        # create and return the metatest_tool
        # TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def _create_meta_test_tool()

    def _create_meta_codecoverage_tool(self):
        # create and return the metacodecoverage_tool
        # TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def _create_meta_codecoverage_tool()

    def _create_meta_mutation_tool(self):
        # create and return the metamutation_tool
        # TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def _create_meta_mutation_tool()

    def _initialize_output_structure(self, cleanstart=False):
        if cleanstart:
            if common_mix.confirm_execution(
                                    "Do you really want to clean the outdir?"):
                self.head_explorer.clean_create_and_get_dir(\
                                            outdir_struct.TOP_OUTPUT_DIR_KEY)
            else:
                ERROR_HANDLER.error_exit("Cancelled Cleanstart!", __file__)
        else:
            self.head_explorer.get_or_create_and_get_dir(\
                                            outdir_struct.TOP_OUTPUT_DIR_KEY)

        for folder in [outdir_struct.CONTROLLER_DATA_DIR, \
                                    outdir_struct.CTRL_CHECKPOINT_DIR, \
                                    outdir_struct.CTRL_LOGS_DIR, \
                                    outdir_struct.EXECUTION_TMP_DIR]:
            self.head_explorer.get_or_create_and_get_dir(folder)
    #~ def _initialize_output_structure()

    def _get_checkpoint_files(self):
        cp_file = self.head_explorer.get_file_pathname(\
                                        outdir_struct.EXECUTION_STATE)
        cp_file_bak = self.head_explorer.get_file_pathname(\
                                        outdir_struct.EXECUTION_STATE_BAKUP)
        return (cp_file, cp_file_bak)
    #~ def _get_checkpoint_files()
#~ class Executor