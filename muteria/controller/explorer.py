
from __future__ import print_function

import os
import logging
import shutil
import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

from muteria.drivers.criteria import TestCriteria

ERROR_HANDLER = common_mix.ErrorHandler

# -----------------------------------------------
# Special
TOP_OUTPUT_DIR_KEY = "main_controller_top_output"

# Directories
## CONSTANTS
CRITERIA_WORKDIR = "criteria_workdir"
TESTSCASES_WORKDIR = "testscases_workdir"
RESULTS_DATA_DIR = "RESULTS_DATA"
RESULTS_MATRICES_DIR = "matrices"
RESULTS_TESTEXECUTION_OUTPUTS_DIR = "testexecution_outputs"
RESULTS_STATS_DIR = "statistics"
OTHER_COPIED_RESULTS = "other_copied_results"

CB_FACTORY_WORKDIR = "code_build_workdir"

CONTROLLER_DATA_DIR = "_controller_dat"
CTRL_CHECKPOINT_DIR = "checkpoint_states"
CTRL_LOGS_DIR = "logs"

EXECUTION_TMP_DIR = "execution_tmp"

# Files
## CONSTANTS
SAVED_CONF = "saved_configuration"
EXECUTION_STATE = "execution_state"
EXECUTION_STATE_BAKUP = "execution_state" + ".bak"
EXECUTION_TIMES = "execution_times"
MAIN_LOG_FILE = "ctrl_log.log"

TEST_PASS_FAIL_MATRIX = "PASSFAIL.csv"
CRITERIA_MATRIX = {}
for criterion in TestCriteria:
    CRITERIA_MATRIX[criterion] = criterion.get_str()+".csv"

STATS_MAIN_FILE_HTML = "main_stats.html"
STATS_MAIN_FILE_JSON = "main_stats.json"

TMP_TEST_PASS_FAIL_MATRIX = "tmp_PASSFAIL.csv"
PARTIAL_TMP_TEST_PASS_FAIL_MATRIX = "partial_tmp_PASSFAIL.csv"
TMP_CRITERIA_MATRIX = {}
for criterion in TestCriteria:
    TMP_CRITERIA_MATRIX[criterion] = "tmp_"+criterion.get_str()+".csv"
PARTIAL_TMP_CRITERIA_MATRIX = {}
for criterion in TestCriteria:
    PARTIAL_TMP_CRITERIA_MATRIX[criterion] = \
                                    "partial_tmp_"+criterion.get_str()+".csv"
TMP_SELECTED_TESTS_LIST = "tmp_selected_test.json"
TMP_SELECTED_CRITERIA_OBJECTIVES_LIST = "tmp_selected_criteria_objectives.json"

# OUTPUT Hashed
PROGRAM_TESTEXECUTION_OUTPUT = "program_output.json" 
TMP_PROGRAM_TESTEXECUTION_OUTPUT = "tmp_program_output.json" 
PARTIAL_TMP_PROGRAM_TESTEXECUTION_OUTPUT = "partial_tmp_program_output.json"
CRITERIA_EXECUTION_OUTPUT = {}
for criterion in TestCriteria:
    CRITERIA_EXECUTION_OUTPUT[criterion] = criterion.get_str()+"_output.json"
TMP_CRITERIA_EXECUTION_OUTPUT = {}
for criterion in TestCriteria:
    TMP_CRITERIA_EXECUTION_OUTPUT[criterion] = \
                                    "tmp_"+criterion.get_str()+"_output.json"
PARTIAL_TMP_CRITERIA_EXECUTION_OUTPUT = {}
for criterion in TestCriteria:
    PARTIAL_TMP_CRITERIA_EXECUTION_OUTPUT[criterion] = \
                            "partial_tmp_"+criterion.get_str()+"_output.json"
# ---------------------------------------------------------

def get_outputdir_structure_by_filesdirs():
    '''
    :returns: The structure of the output directory as directely 
                controlled by this controller. 
                The structure is a 'dict' where keys
                are files or folders and values are None for files and
                another dict for folders.
    '''
    # Dirs
    TopExecutionDir = {
        CRITERIA_WORKDIR: [CRITERIA_WORKDIR],
        TESTSCASES_WORKDIR: [TESTSCASES_WORKDIR],
        RESULTS_DATA_DIR: [RESULTS_DATA_DIR],
        RESULTS_MATRICES_DIR: [RESULTS_DATA_DIR, RESULTS_MATRICES_DIR],
        RESULTS_TESTEXECUTION_OUTPUTS_DIR: [RESULTS_DATA_DIR, \
                                            RESULTS_TESTEXECUTION_OUTPUTS_DIR],
        RESULTS_STATS_DIR: [RESULTS_DATA_DIR, RESULTS_STATS_DIR],
        OTHER_COPIED_RESULTS: [RESULTS_DATA_DIR, OTHER_COPIED_RESULTS],
        CB_FACTORY_WORKDIR: [CB_FACTORY_WORKDIR],
        CONTROLLER_DATA_DIR: [CONTROLLER_DATA_DIR],
        CTRL_CHECKPOINT_DIR: [CONTROLLER_DATA_DIR, CTRL_CHECKPOINT_DIR],
        CTRL_LOGS_DIR: [CONTROLLER_DATA_DIR, CTRL_LOGS_DIR],
        EXECUTION_TMP_DIR: [CONTROLLER_DATA_DIR, EXECUTION_TMP_DIR]
    }

    # Files
    TopExecutionDir[SAVED_CONF] = TopExecutionDir[CTRL_CHECKPOINT_DIR] \
                                    + [SAVED_CONF]
    TopExecutionDir[EXECUTION_STATE] = \
                                    TopExecutionDir[CTRL_CHECKPOINT_DIR] \
                                    + [EXECUTION_STATE]
    TopExecutionDir[EXECUTION_STATE_BAKUP] = \
                                    TopExecutionDir[CTRL_CHECKPOINT_DIR] \
                                    + [EXECUTION_STATE_BAKUP]
    TopExecutionDir[EXECUTION_TIMES] = TopExecutionDir[CONTROLLER_DATA_DIR] \
                                        + [EXECUTION_TIMES]
    TopExecutionDir[MAIN_LOG_FILE] = TopExecutionDir[CTRL_LOGS_DIR] \
                                        + [MAIN_LOG_FILE]

    TopExecutionDir[TEST_PASS_FAIL_MATRIX] = \
                TopExecutionDir[RESULTS_MATRICES_DIR] + [TEST_PASS_FAIL_MATRIX]
    TopExecutionDir[TMP_TEST_PASS_FAIL_MATRIX] = \
                                    TopExecutionDir[RESULTS_MATRICES_DIR] \
                                                + [TMP_TEST_PASS_FAIL_MATRIX]
    TopExecutionDir[PARTIAL_TMP_TEST_PASS_FAIL_MATRIX] = \
                                    TopExecutionDir[RESULTS_MATRICES_DIR] \
                                        + [PARTIAL_TMP_TEST_PASS_FAIL_MATRIX]
    for criterion in TestCriteria:
        TopExecutionDir[CRITERIA_MATRIX[criterion]] = \
                                    TopExecutionDir[RESULTS_MATRICES_DIR] \
                                                + [CRITERIA_MATRIX[criterion]]
        TopExecutionDir[TMP_CRITERIA_MATRIX[criterion]] = \
                                    TopExecutionDir[EXECUTION_TMP_DIR] \
                                            + [TMP_CRITERIA_MATRIX[criterion]]
        TopExecutionDir[PARTIAL_TMP_CRITERIA_MATRIX[criterion]] = \
                                    TopExecutionDir[EXECUTION_TMP_DIR] \
                                    + [PARTIAL_TMP_CRITERIA_MATRIX[criterion]]
    # Output
    TopExecutionDir[PROGRAM_TESTEXECUTION_OUTPUT] = \
                    TopExecutionDir[RESULTS_TESTEXECUTION_OUTPUTS_DIR] + \
                                                [PROGRAM_TESTEXECUTION_OUTPUT]
    TopExecutionDir[TMP_PROGRAM_TESTEXECUTION_OUTPUT] = \
                        TopExecutionDir[RESULTS_TESTEXECUTION_OUTPUTS_DIR] + \
                                            [TMP_PROGRAM_TESTEXECUTION_OUTPUT]
    TopExecutionDir[PARTIAL_TMP_PROGRAM_TESTEXECUTION_OUTPUT] = \
                        TopExecutionDir[RESULTS_TESTEXECUTION_OUTPUTS_DIR] + \
                                    [PARTIAL_TMP_PROGRAM_TESTEXECUTION_OUTPUT]
    for criterion in TestCriteria:
        TopExecutionDir[CRITERIA_EXECUTION_OUTPUT[criterion]] = \
                        TopExecutionDir[RESULTS_TESTEXECUTION_OUTPUTS_DIR] + \
                                        [CRITERIA_EXECUTION_OUTPUT[criterion]]
        TopExecutionDir[TMP_CRITERIA_EXECUTION_OUTPUT[criterion]] = \
                                        TopExecutionDir[EXECUTION_TMP_DIR] + \
                                    [TMP_CRITERIA_EXECUTION_OUTPUT[criterion]]
        TopExecutionDir[PARTIAL_TMP_CRITERIA_EXECUTION_OUTPUT[criterion]] = \
                                    TopExecutionDir[EXECUTION_TMP_DIR] + \
                            [PARTIAL_TMP_CRITERIA_EXECUTION_OUTPUT[criterion]]
    
    TopExecutionDir[TMP_SELECTED_TESTS_LIST] = \
                TopExecutionDir[EXECUTION_TMP_DIR] + [TMP_SELECTED_TESTS_LIST]

    TopExecutionDir[TMP_SELECTED_CRITERIA_OBJECTIVES_LIST] = \
                                TopExecutionDir[EXECUTION_TMP_DIR] \
                                    + [TMP_SELECTED_CRITERIA_OBJECTIVES_LIST]

    TopExecutionDir[STATS_MAIN_FILE_HTML] = TopExecutionDir[RESULTS_STATS_DIR]\
                                                    + [STATS_MAIN_FILE_HTML]

    TopExecutionDir[STATS_MAIN_FILE_JSON] = TopExecutionDir[RESULTS_STATS_DIR]\
                                                    + [STATS_MAIN_FILE_JSON]
                                                    
    return TopExecutionDir
#~ def get_outputdir_structure_by_filesdirs():


class Explorer(common_fs.FileDirStructureHandling):
    def __init__(self, outdir):
        common_fs.FileDirStructureHandling.__init__(self, \
            top_dir=os.path.abspath(outdir), \
            top_dir_key=TOP_OUTPUT_DIR_KEY, \
            file_dir_dict=get_outputdir_structure_by_filesdirs())
    #~ def __init__()
#~ class Explorer

class TopExplorer(object):
    """
    TODO: Handle zipping of history and unzipping...
    Maybe need a zipping explorer?
    """
    LATEST_NAME = "latest"
    HISTORY_PREFIX = 'history'
    def __init__(self, root_outdir):
        self.root_outdir = root_outdir
        self.timeline_outdirs = []

        # get timeline_outdirs
        self.timeline_outdirs.append(os.path.join(self.root_outdir, \
                                                            self.LATEST_NAME))
        
        tmp_outdirs = []
        if os.path.isdir(root_outdir):
            for fd in os.listdir(root_outdir):
                if self._is_history_file_dir(fd):
                    tmp_outdirs.append(os.path.join(self.root_outdir, fd))
        
        tmp_outdirs.sort(key=lambda x: self._history_of_outdir(x))
        tmp_histories = [self._history_of_outdir(x) for x in tmp_outdirs]

        fix_missing_history = False
        for ind in range(len(tmp_histories)):
            new_outdir = tmp_outdirs[ind]
            if tmp_histories[ind] != ind + 1:
                if not fix_missing_history:
                    fix_missing_history = common_mix.confirm_execution(\
                                            "Missing history: {}. {}".format(\
                                ind+1, "Do you want to automatically fix it?"))
                    ERROR_HANDLER.assert_true(fix_missing_history, \
                                    "No history should be missing {}".format(\
                                    "when executing. Fix manually."), __file__)
                else:
                    new_outdir = self._change_history(tmp_outdirs[ind], ind+1)
                    shutil.move(tmp_outdirs[ind], new_outdir)
            self.timeline_outdirs.append(new_outdir)

        # Create explorers
        self.explorer_list = self._create_explorers(self.timeline_outdirs)
    #~ def __init__()

    def get_explorer_list(self, history):
        ERROR_HANDLER.assert_true(history >= 0, \
                                    "Invalid History, must be >=0", __file__)
        ERROR_HANDLER.assert_true(history < len(self.explorer_list), \
                        "Invalid History, must be <= max history", __file__)
        return self.explorer_list[history]
    #~ def get_explorer_list()

    def get_latest_explorer(self):
        return self.explorer_list[0]
    #~ def get_latest_explorer()

    def archive_latest(self):
        new_timeline_outdirs = [self._make_history_name(1)]

        # shift everything
        for history in range(1, len(self.timeline_outdirs)):
            new_timeline_outdirs.append(self._change_history(\
                                    self.timeline_outdirs[history], history+1))

        # moves
        for i in range(len(new_timeline_outdirs)-1, -1, -1):
            shutil.move(self.timeline_outdirs[i], new_timeline_outdirs[i])

        self.timeline_outdirs[1:] = new_timeline_outdirs

        # Re-create explorers
        self.explorer_list = self._create_explorers(self.timeline_outdirs)
    #~ def archive_latest()

    def _create_explorers(self, outdir_list):
        explorer_list = []
        for outdir in outdir_list:
            ERROR_HANDLER.assert_true(outdir.startswith(self.root_outdir),\
                        "outdir {} not in rootdir".format(outdir), __file__)
            explorer_list.append(Explorer(outdir))
        return explorer_list
    #~ def _create_explorers()

    def _make_history_name(self, history, relative=False):
        rel_name = self.HISTORY_PREFIX + "_" + str(history)
        if relative:
            return rel_name
        else:
            return os.path.join(self.root_outdir, rel_name)
    #~ def _make_history_name()

    def _change_history(self, pathname, new_history):
        ERROR_HANDLER.assert_true(self._is_history_file_dir(pathname))
        dir_name, base_name = os.path.split(pathname)
        new_base_name = base_name.replace(\
                                    str(self._history_of_outdir(pathname)), \
                                                        str(new_history), 1)
        new_path_name = os.path.join(dir_name, new_base_name)
        return new_path_name
    #~ def _change_history()

    def _history_of_outdir(self, pathname):
        return int(os.path.basename(pathname).split('_')[1].split('.')[0])
    #~ def _history_of_outdir():

    def _is_history_file_dir(self, pathname):
        parts = os.path.basename(pathname).split('_')
        if len(parts) != 2:
            return False
        if parts[0] != self.HISTORY_PREFIX:
            return False
        if not parts[1].split('.')[0].isdigit():
            return False
        return True
    #~ def _is_history_file_dir()
#~ class TopExplorer