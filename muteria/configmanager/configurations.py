import logging

import muteria.common.mix as common_mix 

ERROR_HANDLER = common_mix.ErrorHandler

# TODO Find way to make the classes so that new elements cannot be added on the fly

RUN_MODE = 0
NAVIGATE_MODE = 1
CLEAN_REVERT_REPOS_MODE = 2
RESTORE_REPOS_MODE = 3

class ExecutionConfig(object):
    PROGRAMMING_LANGUAGE = None

    # Criteria to Include in the analysis
    # The corresponding configs of codecoverage (`CodecoverageToolsConfig`)
    # and mutation (`MutationToolsConfig`) are considered if and only if 
    # the corresponding include is enabled
    INCLUDE_CODECOVERAGE = True
    INCLUDE_MUTATION = True

    # PARALELISM
    SINGLE_REPO_PARALLELISM = 1 # Max number of paralle exec in a repo dir

    # MICRO CONTROLS
    EXECUTE_ONLY_CURENT_CHECKPOINT_META_TASK = False # for Debugging
    RESTART_CURRENT_EXECUTING_META_TASKS = False
    # Specify a Step to go back to
    RE_EXECUTE_FROM_CHECKPOINT_META_TASKS = [] # Make interaction easy
#~class ExecutionConfig

class ReportingConfig(object):
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
#~class ReportingConfig

class ProjectConfig(object):
    OUTPUT_TOP_DIR = None
    REPO_DIR = None
    
    # string representing the relative path to the executable
    # (or entry point file) in the repository
    EXECUTABLE_REPO_RELATIVE_PATH = None

    # Specify the general scope of the evaluation, 
    # Specific scope can be specified per tool
    TARGET_CLASS_NAME = None
    # None value mean all functions
    TARGET_CLASS_TARGET_FUNCTIONS = None
    # None value means all source files
    TARGET_SOURCE_FILES_LIST = None
    # None value means all dev tests
    DEVELOPER_TESTS_LIST = None

    # Function that takes the dev_test name as single input
    # and run with the executable as in repository
    CUSTOM_DEV_TEST_RUNNER = None

    # Function that build the code to execute (for compiled languages)
    # The function has 3 parameters: 
    # <Optional compiler to use> <optional flags to pass to compiler> <clean?>
    # A code builder class is defined and make use of this function 
    # It ensure on call to this functin at the time and no call while any 
    # processing in the repodir. 
    CODE_BUILDER_FUNC = None
#~class ProjectConfig

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
        num_elem = len(self.__dict__)
        super(ToolUserCustom, self).__init__(**kwargs)
        self.__dict__ = self
        diff = len(self.__dict__) - num_elem
        if diff != 0:
            logging.error("{} invalid parameter was/were added".format(diff))
            ERROR_HANDLER.error_exit_file(__file__)
    #~def __init__()
#~class ToolUserCustom

class TestcaseToolsConfig(object):
    # TESTS
    DEVELOPER_TESTS_ENABLED = True
    AUTOMATIC_TESTS_ENABLED = True

    TESTS_ORACLE_TESTS = True
    TESTS_ORACLE_OTHER_VERSION = True

    STOP_TESTS_EXECUTION_ON_FAILURE = False # Will not get full matrix

    DISCARD_FLAKY_TESTS = True

    TEST_GENERATION_TIMEOUT = 7200.0 # in seconds
    ONE_TEST_EXECUTION_TIMEOUT = 900.0 # in seconds (Handle inifnite loops)

    TESTS_GENERATION_TOOLS = []
    DEVELOPER_TESTS_TOOLS = []

    # Reporting
    REPORT_NUMBER_OF_TESTS_GENERATED = True
    REPORT_NUMBER_OF_DUPLICATED_TESTS = True
#~class TestcaseToolsConfig
    
class CodecoverageToolsConfig(object):
    # CODE COVERAGE
    STATEMENT_COVERAGE_ENABLED = True
    BRANCH_COVERAGE_ENABLED = True
    FUNCTION_COVERAGE_ENABLED = True

    ONLY_RUN_FAILING_TESTS_WITH_STATEMENT_COVERAGE = False
    ONLY_RUN_FAILING_TESTS_WITH_BRANCH_COVERAGE = False
    ONLY_RUN_FAILING_TESTS_WITH_FUNCTION_COVERAGE = False

    ONLY_RUN_PASSING_TESTS_WITH_STATEMENT_COVERAGE = False
    ONLY_RUN_PASSING_TESTS_WITH_BRANCH_COVERAGE = False
    ONLY_RUN_PASSING_TESTS_WITH_FUNCTION_COVERAGE = False

    COVERAGE_TEST_EXECUTION_EXTRA_TIMEOUT = 60.0 # in seconds

    ## Tools
    STATEMENT_COVERAGE_TOOL = None
    BRANCH_COVERAGE_TOOL = None
    FUNCTION_COVERAGE_TOOL = None

#~class CodecoverageToolsConfig
    
class MutationToolsConfig(object):
    # MUTATION
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

    ## grace time given to the mutant to complete after the original
    ## execution time has passed
    STRONG_MUTANT_TEST_EXECUTION_EXTRA_TIMEOUT = 60.0 # in seconds
    WEAK_COVERAGE_MUTANT_TEST_EXECUTION_EXTRA_TIMEOUT = 600.0 # in seconds

    ## Tools
    MUTATION_TOOLS = []
#~class MutationToolsConfig
    



class ControlArgsBase(object):
    clean_start = False
    re_execute_from_task = None


class RunControlArgs(ExecutionConfig):

class NavigateControlArgs(ExecutionConfig):

class ReposReverseControlArgs(ExecutionConfig):
    clean_revert = False
    
