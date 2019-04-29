""" This module implements the definition of the different configuration.
    We have a class defined for each configuration type. namely:
        - `ExecutionConfig`: Execution Configuration.
        - `ReportingConfig`: Reporting Configuration.
        - `ProjectConfig`: Project Configuration.
        - `TestcaseToolsConfig`: Testcase Tools Configuration.
        - `CodecoverageToolsConfig`: Codecoverage Tools Configuration.
        - `MutationToolsConfig`: Mutation Tools Configuration.

    TODO: Implement the restriction in adding extra element after creation
    TODO: Implement the verification of the parameters of each config
    TODO: Implement loading the values of the parameters from files... and 
            Checking
"""
#TODO: Implement test tool ordering (who use whose tests)

from __future__ import print_function

import logging

import muteria.common.mix as common_mix 

from muteria.drivers.testgeneration import TestToolType

ERROR_HANDLER = common_mix.ErrorHandler

# TODO Find way to make the classes so that new elements cannot be added on the fly

class SessionMode(common_mix.EnumAutoName):
    EXECUTE_MODE = 0
    VIEW_MODE = 1
    INTERNAL_MODE = 2
    RESTORE_REPOS_MODE = 3
#~ class SessionMode

class ConfigClasses(common_mix.EnumAutoName):
    CONTROLLER_CONF = "CONTROLLER_CONF"
    PROJECT_CONF = "PROJECT_CONF"
    TESTCASES_CONF = "TESTCASES_CONF"
    CRITERIA_CONF = "CRITERIA_CONF"
    OTHER_CONF = "OTHER_CONF"
#~ class ConfigClasses

class ConfigElement(object):
    def __init__(self, val=None, desc=None, val_range=None, conf_class=None):
        self.val = val
        self.desc = desc
        self.val_range = val_range
        self.conf_class = conf_class
    #~ def __self__()

    def set_val(self, new_val):
        self.val = new_val
    def get_val(self):
        return self.val
    
    def set_desc(self, new_desc):
        self.desc = new_desc
    def get_desc(self):
        return self.desc

    def set_val_range(self, new_val_range):
        self.val_range = new_val_range
    def get_val_range(self):
        return self.val_range

    def set_conf_class(self, new_conf_class):
        self.conf_class = new_conf_class
    def get_conf_class(self):
        return self.conf_class
#~ class ConfigElement()

class CompleteConfiguration(object):

    #######################################################
    #######             Execution Parameters         ######
    #######################################################
    # Criteria to Include in the analysis
    # The corresponding configs of codecoverage (`CodecoverageToolsConfig`)
    # and mutation (`MutationToolsConfig`) are considered if and only if 
    # the corresponding include is enabled
    
    # List of enabled criteria 
    # (must have tool specified is specifically enabled)
    # None mean all criteria with tool specified
    ENABLED_CRITERIA = [] 

    # PARALELISM
    SINGLE_REPO_PARALLELISM = 1 # Max number of parallel exec in a repo dir

    # MICRO CONTROLS
    EXECUTE_ONLY_CURENT_CHECKPOINT_META_TASK = False # for Debugging
    RESTART_CURRENT_EXECUTING_META_TASKS = False
    # Specify a Step to go back to
    RE_EXECUTE_FROM_CHECKPOINT_META_TASKS = [] # Make interaction easy

    # Output dir pathname
    OUTPUT_ROOT_DIR = None

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
    # Project programming language
    PROGRAMMING_LANGUAGE = None

    # Repository dir pathname
    REPOSITORY_ROOT_DIR = None
    
    # string representing the relative path to the executable
    # (or entry point file) in the repository
    REPO_EXECUTABLE_RELATIVE_PATH = None

    # optional map between each source and the corresponding intermediate
    # file map (such as object or assembly file for c of .class file for java)
    SOURCE_INTERMEDIATE_CODE_MAP = None

    # Specify the optional general scope of the evaluation, 
    # Specific scope can be specified per tool
    TARGET_CLASSES_NAMES = None
    # None value mean all functions
    TARGET_METHODS_BY_TARGET_CLASSES = None
    # each source file element is the relative path from repos rootdir.
    # None value means all source files
    TARGET_SOURCE_FILES_LIST = None
    # each test file element is the relative path from repos rootdir.
    # None value means all dev tests
    DEVELOPER_TESTS_LIST = None

    # Function that takes 3 arguments:
    #   <test_name: str>
    #   <repos directory rootdir: str>
    #   <Executable relative path: str>
    # and run with the executable as in repository
    # The function return:
    #   0 on passing test
    #   1 on failing test
    #   -1 on error
    CUSTOM_DEV_TEST_RUNNER = None

    # Optional. When not None, the CUSTOM_DEV_TEST_RUNNER is the name of 
    # the function in this file to use
    CUSTOM_DEV_TEST_RUNNER_MODULE = None

    # Function that build the code to execute 
    # (for compiled languages such as C)
    # The function has 5 parameters: 
    #   <repos directory rootdir: str>
    #   <Executable relative path: str>
    #   <Optional compiler to use(compiler name): str> 
    #   <optional flags to pass to compiler: str or list of flags> 
    #   <clean temporary before build: bool>
    #   <reconfigure before build: bool>
    # And returns:
    #   True on success  
    #   False on failure
    # A code builder class is defined and make use of this function 
    # It ensure on call to this functin at the time and no call while any 
    # processing in the repodir. 
    CODE_BUILDER_FUNC = None

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
    # >>> TestcaseToolConfig(tooltype=TestToolType.USE_ONLY_CODE,
    #                        toolname='klee', config_id=0)
    TESTCASE_TOOLS_CONFIGS = [

    ]

    # Reporting
    REPORT_NUMBER_OF_TESTS_GENERATED = True
    REPORT_NUMBER_OF_DUPLICATED_TESTS = True

    ## --- Modifiable (Testcase) ---##
    # use test case oracle as oracle
    TESTS_ORACLE_TESTS = True
    # Use output of the specified version as oracle, 
    # Pass filepath to repo patch 
    TESTS_ORACLE_OTHER_VERSION = None
    # file path to an executable to use as oracle
    TESTS_ORACLE_OTHER_EXECUTABLE = None

    TEST_GENERATION_TIMEOUT = 7200.0 # in seconds
    ONE_TEST_EXECUTION_TIMEOUT = 900.0 # in seconds (Handle inifnite loops)
    # ========================================================#

    # ===================== CODE COVERAGE =====================#
    STATEMENT_COVERAGE_ENABLED = True
    BRANCH_COVERAGE_ENABLED = True
    FUNCTION_COVERAGE_ENABLED = True

    RUN_FAILING_TESTS_WITH_STATEMENT_COVERAGE = True
    RUN_FAILING_TESTS_WITH_BRANCH_COVERAGE = True
    RUN_FAILING_TESTS_WITH_FUNCTION_COVERAGE = True

    RUN_PASSING_TESTS_WITH_STATEMENT_COVERAGE = True
    RUN_PASSING_TESTS_WITH_BRANCH_COVERAGE = True
    RUN_PASSING_TESTS_WITH_FUNCTION_COVERAGE = True

    ## Tools
    STATEMENT_COVERAGE_TOOLS = []
    BRANCH_COVERAGE_TOOLS = []
    FUNCTION_COVERAGE_TOOLS = []

    ## --- Modifiable (Code) ---##
    COVERAGE_TEST_EXECUTION_EXTRA_TIMEOUT = 60.0 # in seconds
    # ========================================================#

    # ======================= MUTATION =======================#
    MUTANT_COVERAGE_ENABLED = True
    WEAK_MUTATION_ENABLED = True
    STRONG_MUTATION_ENABLED = True

    STRONG_MUTANTION_ORACLE_TESTS = True
    STRONG_MUTANTION_ORACLE_ORIGINAL = True
    STRONG_MUTANTION_ORACLE_OTHER_VERSION = True

    MUTATION_RESTRICTION_ENABLED = True  # Enable restricting mutation(scope)
    MUTANT_SELECTION_ENABLED = True
    ONLY_EXECUTE_SELECTED_MUTANTS = True

    TRIVIAL_COMPILER_EQUIVALENCE_ENABLED = True

    OPTIMIZE_STRONG_MUTATION_WITH_WEAK_MUTATION = True
    OPTIMIZE_STRONG_MUTATION_WITH_MUTANT_COVERAGE = False
    OPTIMIZE_STRONG_MUTATION_WITH_STATEMENT_COVERAGE = False
    OPTIMIZE_STRONG_MUTATION_WITH_FUNCTION_COVERAGE = False

    STOP_MUTANT_EXECUTION_AT_FIRST_KILL = False # Will not get full matrix.

    ONLY_RUN_FAILING_TESTS_WITH_MUTATION = False
    ONLY_RUN_PASSING_TESTS_WITH_MUTATION = False

    ## Tools
    MUTATION_TOOLS = []

    ## --- Modifiable (Mutation) ---##
    ## grace time given to the mutant to complete after the original
    ## execution time has passed
    STRONG_MUTANT_TEST_EXECUTION_EXTRA_TIMEOUT = 60.0 # in seconds
    WEAK_COVERAGE_MUTANT_TEST_EXECUTION_EXTRA_TIMEOUT = 600.0 # in seconds
    # ========================================================#

    #######################################################
    #######             Extra parameters             ######
    #######################################################
    LLVM_TO_NATIVE_LINKING_FLAGS = None
#~ class CompleteConfiguration

class BaseToolConfig(dict):
    def __init__(self, tooltype=None, toolname=None, config_id=None, \
                                                        tool_user_custom=None):
        self.tooltype = tooltype
        self.toolname = toolname
        self.config_id = config_id
        self.tool_user_custom=tool_user_custom
        if self.config_id is None:
            self.toolalias = self.toolname
        else:
            self.toolalias = toolname+"_"+str(self.config_id)
    #~ def __init__()

    def __eq__(self, value):
        return (self.__dict__ == value.__dict__)

    def get_tool_name(self):
        return self.toolname
    def get_tool_config_alias(self):
        return self.toolalias
    def get_tool_type(self):
        return self.tooltype
#~ class BaseToolConfig

class ToolUserCustom(dict):
    '''
    This config file is helpful to specify tool specific configurations
    For example:
    >>> conf = ToolUserCustom( \
        PATH_TO_TOOL_EXECUTABLE='/fullpath/to/tool/dir', \
        ENV_VARS_DICT={'var1': 'value1'}, \
        PRE_TARGET_CMD_ORDERED_FLAGS_LIST=[('-solver', 'stp'), \
                    ('-mutation-scope', os.path.abspath("scopefile"))], \
        POST_TARGET_CMD_ORDERED_FLAGS_LIST=[('-sym-args', '0', '2', '3')]
    )

    Note: It is possibled to only specify a subset of the values.
    '''
    # -str- custom path to executable parent dir to use for tool.
    # Directory containing executables (fullpath: string)
    # Useful especially for tools having many executables like 'klee'
    PATH_TO_TOOL_BINARY_DIR = None
    # -dict- key value of <environment var: var value> both strings
    ENV_VARS_DICT = None
    # -list of tuples- ordered list of tuples, each tuple represent a flag
    # as first element and its values. ordering is kept
    # example: for GNU find, we can have:
    # [('-type', 'f'), ('-exec', 'grep', '{}', '\\;')]
    # PRE_TARGET_... is the arguments list that must go before the 
    # analyzed program (target) in command line order POST_TARGET go after. 
    PRE_TARGET_CMD_ORDERED_FLAGS_LIST = None
    POST_TARGET_CMD_ORDERED_FLAGS_LIST = None

    def __init__(self, **kwargs):
        num_elem = len(self)
        super(ToolUserCustom, self).__init__(**kwargs)
        self.__dict__ = self
        diff = len(self.__dict__) - num_elem
        if diff != 0:
            ERROR_HANDLER.error_exit(\
                        "{} invalid parameter was/were added".format(diff), \
                                                                    __file__)
    #~def __init__()
#~class ToolUserCustom


class TestcaseToolsConfig(BaseToolConfig):
    # use test case oracle as oracle
    TESTS_ORACLE_TESTS = True
    # Use output of the specified version as oracle, 
    # Pass filepath to repo patch 
    TESTS_ORACLE_OTHER_VERSION = None
    # file path to an executable to use as oracle
    TESTS_ORACLE_OTHER_EXECUTABLE = None

    TEST_GENERATION_TIMEOUT = 7200.0 # in seconds
    ONE_TEST_EXECUTION_TIMEOUT = 900.0 # in seconds (Handle inifnite loops)
#~class TestcaseToolsConfig
    
class CodecoverageToolsConfig(BaseToolConfig):
    COVERAGE_TEST_EXECUTION_EXTRA_TIMEOUT = 60.0 # in seconds
#~class CodecoverageToolsConfig
    
class MutationToolsConfig(BaseToolConfig):
    ## grace time given to the mutant to complete after the original
    ## execution time has passed
    STRONG_MUTANT_TEST_EXECUTION_EXTRA_TIMEOUT = 60.0 # in seconds
    WEAK_COVERAGE_MUTANT_TEST_EXECUTION_EXTRA_TIMEOUT = 600.0 # in seconds
#~class MutationToolsConfig