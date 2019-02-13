""" Thir module defines the files and directory as organized in the 
    output directory
"""

from __future__ import print_function

# Directories
## CONSTANTS
TOP_OUTPUT_DIR_KEY = "main_controller_top_output"

MUTATION_WORKDIR = "mutation_workdir"
CODECOVERAGE_WORKDIR = "codecoverage_workdir"
TESTSCASES_WORKDIR = "testscases_workdir"
RESULTS_DATA_DIR = "RESULTS_DATA"
RESULTS_MATRICES_DIR = "matrices"
RESULTS_STATS_DIR = "statistics"

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
STMT_COVERAGE_MATRIX = "STMT.csv"
BRANCH_COVERAGE_MATRIX = "BRANCH.csv"
FUNCTION_COVERAGE_MATRIX = "FUNCTION.csv"
SM_MATRIX = "SM.csv"
WM_MATRIX = "WM.csv"
MCOV_MATRIX = "MCOV.csv"

STATS_MAIN_FILE_MD = "main_stats.md"

TMP_TEST_PASS_FAIL_MATRIX = "tmp_PASSFAIL.csv"
TMP_STMT_COVERAGE_MATRIX = "tmp_STMT.csv"
TMP_BRANCH_COVERAGE_MATRIX = "tmp_BRANCH.csv"
TMP_FUNCTION_COVERAGE_MATRIX = "tmp_FUNCTION.csv"
TMP_SM_MATRIX = "tmp_SM.csv"
TMP_WM_MATRIX = "tmp_WM.csv"
TMP_MCOV_MATRIX = "tmp_MCOV.csv"

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
        MUTATION_WORKDIR: [MUTATION_WORKDIR],
        CODECOVERAGE_WORKDIR: [CODECOVERAGE_WORKDIR],
        TESTSCASES_WORKDIR: [TESTSCASES_WORKDIR],
        RESULTS_DATA_DIR: [RESULTS_DATA_DIR],
        RESULTS_MATRICES_DIR: [RESULTS_DATA_DIR, RESULTS_MATRICES_DIR],
        RESULTS_STATS_DIR: [RESULTS_DATA_DIR, RESULTS_STATS_DIR],
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

    for m_file in [TEST_PASS_FAIL_MATRIX, STMT_COVERAGE_MATRIX, 
                    BRANCH_COVERAGE_MATRIX, FUNCTION_COVERAGE_MATRIX, 
                    SM_MATRIX, WM_MATRIX, MCOV_MATRIX]:
        TopExecutionDir[m_file] = TopExecutionDir[RESULTS_MATRICES_DIR] \
                                                                    + m_file

    TopExecutionDir[STATS_MAIN_FILE_MD] = TopExecutionDir[RESULTS_STATS_DIR] \
                                                    + STATS_MAIN_FILE_MD
                                                    
    for tm_file in [TMP_TEST_PASS_FAIL_MATRIX, TMP_STMT_COVERAGE_MATRIX, 
                    TMP_BRANCH_COVERAGE_MATRIX, TMP_FUNCTION_COVERAGE_MATRIX,
                    TMP_SM_MATRIX, TMP_WM_MATRIX, TMP_MCOV_MATRIX]:
        TopExecutionDir[tm_file] = TopExecutionDir[EXECUTION_TMP_DIR] \
                                                                    + tm_file

    return TopExecutionDir

#~ def get_outputdir_structure_by_filesdirs():