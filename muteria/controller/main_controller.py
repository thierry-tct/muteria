"""
This module implement the main controller class, which is the entry point
of the execution.
The entry class is `MainController` and the entrypoint method is 
`MainController.mainrun`

TODO:
    0. write the out directory structure component properly 
        (This is shared between the 3 modes: RUN, REVERT and NAVIGATE)

    Pipeline:
    1. load the default configuration.
    2. parse the command lines, then load the users config, then update the
        default configs.
    3. setup the ERROR_HANDLER module (pass the repodir).
    4. setup the log facility.
    5. based on the loaded config and command mode, call the relevant 
        mode executor with its configs. (RUN, REVERT, NAVIGATE)

    a) RUN will implement checkpoint and run tasks....
"""

from __future__ import print_function
import os, sys
import glob
import copy

import importlib
import logging

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices

import muteria.configmanager.configurations as configurations
from muteria.configmanager.helper import ConfigurationHelper
from muteria.repositoryandcode.repository_manager import RepositoryManager

# from this package
import muteria.controller.logging_setup as logging_setup
import muteria.controller.explorer as explorer
import muteria.controller.executor as executor

ERROR_HANDLER = common_mix.ErrorHandler

class MainController (object):
    '''
    This class implements the main controlle which will organize the execution
    and reporting.

    :param execution_config: Configuration data for execution setting (such as:
                            execution order, what to execute, ...)
    :param reporting_config: Configuration for reporting (coverage, 
                            mutation score, ...)
    :param tools_config: Configurations of the tools involved (test tool, 
                            mutation tool, code coverage tools)
    :param project_config: Configurations of the project to analyze
    :param output_pathdir: Path to the directory where the execution take place
                            and the resulting data are stored.
    '''
    def __init__(self): 
        # Set the logger temporarily (before the log file can be dispo)
        logging_setup.console_tmp_log_setup()
    #~ def __init__()

    def internal_infos(self, config):
        # TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def internal_infos()

    def view(self, top_timeline_explorer, config):
        '''
        Method used to navigate in the output dir and make simple queries
        '''
        # TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the View")
    #~ def view()

    #def log_run_summary(self):
    #    '''
    #    Log information showing a new run of resume of previous run
    #    '''

    def raw_config_main(self, raw_config):
        """
        TODO: Deal with config change at different runs
                Notify the user that the config changed and show the diff
        TODO: add option to load the config from prev if not specified()
        """
        # Create config from raw config
        final_conf = ConfigurationHelper.get_finalconf_from_rawconf(\
                                                        raw_conf=raw_config)

        # Call main with the result of raw config
        self.main(final_config=final_conf)
    #~ def raw_config_main()

    def main(self, final_config):
        '''
        Entry point function using the final configuration object
        '''
        # XXX Create TopExplorer
        top_timeline_explorer = explorer.TopExplorer(\
                                        final_config.OUTPUT_ROOT_DIR.get_val())

        # XXX Actual Execution based on the mode
        mode = final_config.RUN_MODE.get_val()

        if mode == configurations.SessionMode.EXECUTE_MODE:
            # Executor
            # XXX Main Execution
            exec_obj = executor.Executor(final_config, top_timeline_explorer)
            exec_obj.main()
        elif mode == configurations.SessionMode.RESTORE_REPOS_MODE:
            # Restore the project repo dir's files that could have been changed.
            # This do not remove the possibly added files or folders
            as_initial = final_config.restore.AS_INITIAL.get_val()
            repo_mgr = executor.Executor.create_repo_manager(final_config)
            repo_mgr.revert_repository(as_initial=as_initial)
        elif mode == configurations.SessionMode.VIEW_MODE:
            # View
            self.view(top_timeline_explorer, final_config)
        elif mode == configurations.SessionMode.INTERNAL_MODE:
            # Internal Helpers
            self.internal_infos(final_config)
        logging.info("All Done!")
    #~ def main()
#~ class MainController
