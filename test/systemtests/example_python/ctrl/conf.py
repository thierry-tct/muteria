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

this_dir = os.path.dirname(os.path.abspath(__file__))

devtestlist = ['test_lib.py']
def dev_test_runner(test_name, repo_root_dir, exe_path_map, env_vars, timeout):
    # TODO: use exe_path_map

    def parse_test(s):
        return s.split('...')[0].replace(':','/').replace(' ','')

    if test_name == 'test_lib.py':
        #TODO fix it
        cwd = os.getcwd()
        os.chdir(repo_root_dir)

        try:
            args_list = ['-m', 'unittest', test_name, '-v']
            retcode, _, stderr = DriversUtils.execute_and_get_retcode_out_err(\
                                    prog=sys.executable, args_list=args_list, \
                                    timeout=timeout, out_on=False)
            stderr = stderr.splitlines()
        except:
            # ERROR
            os.chdir(cwd)
            return GlobalConstants.TEST_EXECUTION_ERROR
        
        # Parse the result
        subtests_verdicts = {}
        hasfail = False
        hasfail |= (retcode != 0)
        for s in stderr:
            if s.endswith('... FAIL'):
                hasfail = True
                subtests_verdicts[parse_test(s)] = True
            elif s.endswith('... ok'):
                subtests_verdicts[parse_test(s)] = False
        #print(subtests_verdicts)
        os.chdir(cwd)
        return GlobalConstants.FAIL_TEST_VERDICT if hasfail else \
                                            GlobalConstants.PASS_TEST_VERDICT
    # ERROR
    return GlobalConstants.TEST_EXECUTION_ERROR

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