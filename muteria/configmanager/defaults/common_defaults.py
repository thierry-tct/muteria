""" Defaults parameters that are common to all languages
"""
from __future__ import print_function

from muteria.configmanager.configurations import SessionMode
from muteria.configmanager.configurations import TestcaseToolsConfig
from muteria.configmanager.configurations import CriteriaToolsConfig
from muteria.configmanager.configurations import ToolUserCustom

from muteria.drivers.criteria import TestCriteria
from muteria.drivers.criteria import CriteriaToolType

from muteria.drivers.testgeneration import TestToolType


#######################################################
#######             Execution Parameters         ######
#######################################################
# Criteria to Include in the analysis
# The corresponding configs of codecoverage (`CodecoverageToolsConfig`)
# and mutation (`MutationToolsConfig`) are considered if and only if
# the corresponding include is enabled

# Decide whether to start over, deleting previous, for execution mode
EXECUTION_CLEANSTART=False

# Value of type SessionMode (Mandatory)
RUN_MODE = None

# List of enabled criteria
# (must have tool specified is specifically enabled)
# None mean all criteria with tool specified
ENABLED_CRITERIA = []

# Enable keeping output summary for program passfail execution
GET_PASSFAIL_OUTPUT_SUMMARY = True

# keepoutput summary for the following criteria (may run slower)
CRITERIA_WITH_OUTPUT_SUMMARY = []

# PARALELISM
SINGLE_REPO_PARALLELISM = 1 # Max number of parallel exec in a repo dir

# MICRO CONTROLS
EXECUTE_ONLY_CURENT_CHECKPOINT_META_TASK = False # for Debugging
RESTART_CURRENT_EXECUTING_META_TASKS = False
# Specify a Step to go back to
RE_EXECUTE_FROM_CHECKPOINT_META_TASKS = [] # Make interaction easy

# Output dir pathname (Mandatory)
OUTPUT_ROOT_DIR = None

# Enable logging debug data
LOG_DEBUG = False

#######################################################
#######             Reporting Parameters         ######
#######################################################
GENERATE_HTML_REPORT = True

OUTPUT_CRITERIA_SCORES = True
CRITERIA_SCORE_BY_TOOL = True
OUTPUT_CRITERIA_SUBSUMPTION_SCORE = True

OUTPUT_CRITERIA_COVERED_ELEMENTS = False
OUTPUT_CRITERIA_UNCOVERED_ELEMENTS = True
DETAILED_ELEMENTS_OUTPUT = False

OUTPUT_CRITERIA_SUBSUMING_ELEM_NUM = True

# When iteratively try to cover some element, show
OUTPUT_STATS_HISTORY = True

#######################################################
#######        Project Config Parameters         ######
#######################################################
# Project programming language (Mandatory)
PROGRAMMING_LANGUAGE = None

# Repository dir pathname (Mandatory)
REPOSITORY_ROOT_DIR = None

# string representing the relative path to the executable
# (or entry point file) in the repository
REPO_EXECUTABLE_RELATIVE_PATHS = None

# optional map between each source and the corresponding intermediate
# file map (such as object or assembly file for c of .class file for java)
TARGET_SOURCE_INTERMEDIATE_CODE_MAP = None

# Specify the optional general scope of the evaluation,
# Specific scope can be specified per tool
TARGET_CLASSES_NAMES = None
# None value mean all functions
TARGET_METHODS_BY_TARGET_CLASSES = None
# each source file element is the relative path from repos rootdir.
# None value means all source files
##TARGET_SOURCE_FILES_LIST = None

# each test file element is the relative path from repos rootdir.
# None value means all dev tests
DEVELOPER_TESTS_LIST = None

# Function that takes 3 arguments:
#   <test_name: str>
#   <repos directory rootdir: str>
#   <Executable relative path map: dict>
#   <env_vars: map>
#   <timeout: int>
# and run with the executable as in repository
# The function return:
#   0 on passing test
#   1 on failing test
#   -1 on error
CUSTOM_DEV_TEST_RUNNER_FUNCTION = None

CUSTOM_DEV_TEST_PROGRAM_WRAPPER_CLASS = None

# Optional. When not None, the CUSTOM_DEV_TEST_RUNNER is the name of
# the function in this file to use
CUSTOM_DEV_TEST_RUNNER_MODULE = None

# Function that build the code to execute
# (for compiled languages such as C)
# The function has 5 parameters:
#   <repos directory rootdir: str>
#   <Executable relative path: str>
#   <Optional compiler to use(compiler name): str>
#   <optional flags to pass to compiler: list of flags>
#   <clean temporary before build: bool>
#   <reconfigure before build: bool>
# And returns:
#   True on success
#   False on failure
# A code builder class is defined and make use of this function
# It ensure on call to this functin at the time and no call while any
# processing in the repodir.
CODE_BUILDER_FUNCTION = None

# Optional. When not None, the CODE_BUILDER_FUNC is the name of
# the function in this file to use
CODE_BUILDER_MODULE = None

#######################################################
#######             Tools parameters             ######
#######################################################
# ===================== TESTCASES =====================#
# Tests already existing before execution starts
DEVELOPER_TESTS_ENABLED = True
# Test created during execution
GENERATED_TESTS_ENABLED = True

STOP_TESTS_EXECUTION_ON_FAILURE = False # Will not get full matrix

DISCARD_FLAKY_TESTS = True

# Test tool types in order of execution (Test generation).
# elements in same tuple have parallel execution. elements at tuple i
# generate tests after element at i-1 and may use results of test from i-1.
TEST_TOOL_TYPES_SCHEDULING = [
(TestToolType.USE_ONLY_CODE,),
(TestToolType.USE_CODE_AND_TESTS,),
]

# Test generation tool. Example:
# >>> TestcaseToolsConfig(tooltype=TestToolType.USE_ONLY_CODE,
#                        toolname='klee', config_id=0)
TESTCASE_TOOLS_CONFIGS = [

]

# Reporting
REPORT_NUMBER_OF_TESTS_GENERATED = True
REPORT_NUMBER_OF_DUPLICATED_TESTS = True

## --- Modifiable (Testcase) ---##
# use test case oracle as oracle
#TESTS_ORACLE_TESTS = True
# Use output of the specified version as oracle,
# Pass filepath to repo patch
#TESTS_ORACLE_OTHER_VERSION = None
# file path to an executable to use as oracle
#TESTS_ORACLE_OTHER_EXECUTABLE = None

#TEST_GENERATION_TIMEOUT = 7200.0 # in seconds
#ONE_TEST_EXECUTION_TIMEOUT = 900.0 # in seconds (Handle inifnite loops)
# ========================================================#

# ===================== CRITERIA COVERAGE =====================#

# Map with key criteria and values the list of tools
# criteria tool. Example:
# >>> CriteriaToolConfig(tooltype=CriteriaToolType.USE_ONLY_CODE,
#                        toolname='gcov', config_id=0)
CRITERIA_TOOLS_CONFIGS_BY_CRITERIA = {

}

# List of sets of test criteria stating the order in which criteria
# should be executed. Example strom mutation after weak mutation.
# When None, Default to the order in:
# >>> muteria.drivers.criteria.CRITERIA_SEQUENCE
CRITERIA_SEQUENCE = None

# List of criteria that have test objectives covered when test execution
# differs with original
# When None, Default to the order in:
# >>> muteria.drivers.criteria.CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM
CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM = None

# List of criteria to run with failing tests
RUN_FAILING_TESTS_WITH_CRITERIA = [

]

# List of criteria to run with passing tests
RUN_PASSING_TESTS_WITH_CRITERIA = [

]

CRITERIA_RESTRICTION_ENABLED = True  # Enable restricting mutation(scope)

# criterion: selection tools. Example: SM and TCE of E-SELECTIVE
CRITERIA_ELEM_SELECTIONS = {

}

ONLY_EXECUTE_SELECTED_CRITERIA_ELEM = True

MAX_CRITERIA_ELEM_SELECTION_NUM_PERCENT = '100%'

# Criterion: guider dict. ex: {STRONG_MUTATION: Surviving}
CRITERIA_TESTGEN_GUIDANCE = {

}

# Criterion: optimizers dict. ex: {STRONG_MUTATION: SM_OPTIMIZED_BY_WM}
CRITERIA_EXECUTION_OPTIMIZERS = {

}

# Will not get full matrix. the non executed will be uncertain
COVER_CRITERIA_ELEMENTS_ONCE = False

## --- Modifiable (Code) ---##
#SEPARATED_TEST_EXECUTION_EXTRA_TIMEOUT_TIMES = 60.0 # in seconds
#META_TEST_EXECUTION_EXTRA_TIMEOUT_TIMES = 600.0 # in seconds
# ========================================================#

#######################################################
#######             Extra parameters             ######
#######################################################
#LLVM_TO_NATIVE_LINKING_FLAGS = None
