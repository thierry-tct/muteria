import logging

# TODO Find way to make the classes so that new elements cannot be added on the fly

RUN_MODE = 0
NAVIGATE_MODE = 1
CLEAN_REVERT_REPOS_MODE = 2
RESTORE_REPOS_MODE = 3

class ExecutionConfig(object):
    PROGRAMMING_LANGUAGE = None

    
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


    # PARALELISM
    SINGLE_REPO_PARALLELISM = 1 # Max number of paralle exec in a repo dir


    # MICRO CONTROLS
    EXECUTE_ONLY_CURENT_CHECKPOINT_META_TASK = False # for Debugging
    RESTART_CURRENT_EXECUTING_META_TASKS = False
    # Specify a Step to go back to
    RE_EXECUTE_FROM_CHECKPOINT_META_TASKS = [] # Make interaction easy

    
class ControlArgsBase(object):
    clean_start = False
    re_execute_from_task = None


class RunControlArgs(ExecutionConfig):

class NavigateControlArgs(ExecutionConfig):

class ReposReverseControlArgs(ExecutionConfig):
    clean_revert = False
    
