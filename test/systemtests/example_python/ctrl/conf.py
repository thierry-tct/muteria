import os
import sys
import subprocess

from muteria.configmanager.configurations import SessionMode
from muteria.configmanager.configurations import TestcaseToolsConfig
from muteria.configmanager.configurations import CriteriaToolsConfig
from muteria.drivers.testgeneration import TestToolType
from muteria.drivers.criteria import CriteriaToolType
from muteria.drivers.criteria import TestCriteria
from muteria.common.mix import GlobalConstants

from muteria.drivers.testgeneration.testcase_formats.python_unittest \
                                                import python_unittest_runner

this_dir = os.path.dirname(os.path.abspath(__file__))

devtestlist = ['test_lib.py']
def dev_test_runner(test_name, *args, **kwargs):
    if test_name == 'test_lib.py':
        return python_unittest_runner(test_name, *args, **kwargs)

    # ERROR
    return GlobalConstants.TEST_EXECUTION_ERROR
#~ def dev_test_runner()
### 

PROGRAMMING_LANGUAGE='pythOn'
REPOSITORY_ROOT_DIR=os.path.join(os.path.dirname(this_dir), 'repo')
OUTPUT_ROOT_DIR=os.path.join(os.path.dirname(this_dir), 'ctrl', "output")
RUN_MODE=SessionMode.EXECUTE_MODE

TARGET_SOURCE_INTERMEDIATE_CODE_MAP = {'lib/lib.py':None, 'main.py':None}

CUSTOM_DEV_TEST_RUNNER_FUNCTION = dev_test_runner
DEVELOPER_TESTS_LIST = devtestlist

TESTCASE_TOOLS_CONFIGS = [
        TestcaseToolsConfig(tooltype=TestToolType.USE_ONLY_CODE, toolname='custom_devtests', config_id=0),
]

ENABLED_CRITERIA = [
        TestCriteria.STATEMENT_COVERAGE, 
        TestCriteria.BRANCH_COVERAGE,
]

cov_py = CriteriaToolsConfig(tooltype=CriteriaToolType.USE_ONLY_CODE, toolname='coverage_py', config_id=0)
CRITERIA_TOOLS_CONFIGS_BY_CRITERIA = {crit: [cov_py] for crit in ENABLED_CRITERIA} 