"""
This module implement the main controller class, whic is the entry point
of the execution.
The entry class is `MainController` and the entrypoint method is 
`MainController.mainrun`

TODO:
    0. write the out directory structure component properly 
        (This is shared between the 3 modes: RUN, REVERT and NAVIGATE)

    Pipiline:
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

import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices

from muteria.configmanager.configurations import ExecutionConfig
from muteria.configmanager.configurations import ReportingConfig
from muteria.configmanager.configurations import MutationToolsConfig
from muteria.configmanager.configurations import TestcaseToolsConfig
from muteria.configmanager.configurations import CodecoverageToolsConfig
from muteria.configmanager.configurations import ProjectConfig
from muteria.configmanager.configurations import ToolUserCustom

# from this package
import logging_setup


# Directories
## CONSTANTS
TOP_OUTPUT_DIR_KEY = "main_controller_top_output"

MUTATION_WORKDIR = "mutation_workdir"
CODECOVERAGE_WORKDIR = "codecoverage_workdir"
TESTSCASES_WORKDIR = "testscases_workdir"
RESULTS_DATA_DIR = "RESULTS_DATA"
RESULTS_MATRICES = "matrices"
RESULTS_STATS = "statistics"

CONTROLLER_DATA = "_controller_data"
CTRL_CHECKPOINT_DIR = "checkpoint_states"
CTRL_LOGS = "logs"

# Files
## CONSTANTS
SAVED_CONF = "saved_configuration"
EXECUTION_STATE = "execution_state"
EXECUTION_STATE_BAKUP = "execution_state" + ".bak"
EXECUTION_TIMES = "execution_times"
LOG_FILE = "ctrl_log.log"


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
    def __init__(self, execution_config=None, reporting_config=None, \
                    tools_config=None, project_config=None, \
                    output_pathdir=None):
        self.execution_config = execution_config
        self.reporting_config = reporting_config
        self.tools_config = tools_config
        self.project_config = project_config
        self.output_pathdir = output_pathdir

        for v, T, e in [ \
                 (self.execution_config, ExecutionConfig, 'execution_config'), 
                 (self.reporting_config, ReportingConfig, 'reporting_config'), 
                 (self.tools_config, TestcaseToolsConfig, \
                                                    'testcasetools_config'), 
                 (self.tools_config, CodecoverageToolsConfig, \
                                                'codecoveragetools_config'), 
                 (self.tools_config, MutationToolsConfig, \
                                                    'mutationtools_config'), 
                 (self.project_config, ProjectConfig, 'project_config')]: 
            assert type(v) == T, "%s %s" % ("Invalid", e)


        #self.alerter = Alerter ... # error_exit, warning, ...

        output_structure = self.get_outputdir_structure_by_filesdirs()
        self.top_execution_struct = common_fs.FileDirStructureHandling(\
                                                        output_pathdir, \
                                                        TOP_OUTPUT_DIR_KEY, \
                                                        output_structure)

        # Set the logger temporarily (before the log file can be dispo)
        logging_setup.console_tmp_log_setup()
        self.logger_is_set = False

        self.task_scheduler = ... #TODO TaskScheduler(self.execution_config, self.project_config) # extend the checkpointing class

    def get_outputdir_structure_by_filesdirs(self):
        '''
        :returns: The structure of the output directory as directely 
                    controlled by this controller. 
                    The structure is a 'dict' where keys
                    are files or folders and values are None for files and
                    another dict for folders.
        '''
        TopExecutionDir = {
            MUTATION_WORKDIR: [MUTATION_WORKDIR],
            CODECOVERAGE_WORKDIR: [CODECOVERAGE_WORKDIR],
            TESTSCASES_WORKDIR: [TESTSCASES_WORKDIR],
            RESULTS_DATA_DIR: [RESULTS_DATA_DIR],
            RESULTS_MATRICES: [RESULTS_DATA_DIR, RESULTS_MATRICES],
            RESULTS_STATS: [RESULTS_DATA_DIR, RESULTS_STATS],
            CONTROLLER_DATA: [CONTROLLER_DATA],
            CTRL_CHECKPOINT_DIR: [CONTROLLER_DATA, CTRL_CHECKPOINT_DIR],
            CTRL_LOGS: [CONTROLLER_DATA, CTRL_LOGS],
        }

        TopExecutionDir[SAVED_CONF] = TopExecutionDir[CTRL_CHECKPOINT_DIR] \
                                        + [SAVED_CONF]
        TopExecutionDir[EXECUTION_STATE] = \
                                        TopExecutionDir[CTRL_CHECKPOINT_DIR] \
                                        + [EXECUTION_STATE]
        TopExecutionDir[EXECUTION_STATE_BAKUP] = \
                                        TopExecutionDir[CTRL_CHECKPOINT_DIR] \
                                        + [EXECUTION_STATE_BAKUP]
        TopExecutionDir[EXECUTION_TIMES] = TopExecutionDir[CONTROLLER_DATA] \
                                            + [EXECUTION_TIMES]
        TopExecutionDir[LOG_FILE] = TopExecutionDir[CTRL_LOGS] + [LOG_FILE]

        return TopExecutionDir

    def navigate(self):
        '''
        Method used to navigate in the output dir and make simple queries
        '''

    def clean_revert_repos(self):
        '''
        Restore the project repo dir to the initial state,
        This restore possibly changed files or folders and remove 
        possibly added ones. (delete created branch)
        '''

    def restore_repos_files(self):
        '''
        Restore the project repo dir's files that could have been changed.
        This do not remove the possibly added files or folders
        '''

    def extract_cmd_arguments(self):
        '''
        Extract the command line argument, return the execution configs
        '''

    def log_run_summary(self):
        '''
        Log information showing a new run of resume of previous run
        '''

    def mainrun(self):
        '''
        Entry point function
        Method that extract the cmd arguments, 
        run all the tasks set in the configuration
        '''
        # XXX Parse the arguments and return the configs 
        
        # If clean ore restore repos
        # Else If navigate
        # Else 
        #       If cleanstart, ask and clean
        #       Else 
        #               Check consistency with previous of configs
        #       continue running

        # Check or create out dir as well as controller dirs, time and log dir

        # Setup the logger
        if not self.logger_is_set:
            logging_setup.setup(logfile=self.top_execution_struct)
            self.logger_is_set = True

        # XXX Actual Execution

