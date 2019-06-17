import os
import subprocess

from muteria.configmanager.configurations import SessionMode
from muteria.configmanager.configurations import TestcaseToolsConfig
from muteria.configmanager.configurations import CriteriaToolsConfig
from muteria.drivers.testgeneration import TestToolType
from muteria.drivers.criteria import CriteriaToolType
from muteria.drivers.criteria import TestCriteria

this_dir = os.path.dirname(os.path.abspath(__file__))

devtestlist = ['test_lib.sh']
def dev_test_runner(test_name, repo_root_dir, exe_path_map):
    # TODO: use exe_path_map

    if test_name == 'test_lib.sh':
        #TODO fix it
        cwd = os.getcwd()
        os.chdir(repo_root_dir)

        try:
            args_list = [test_name]
            p = subprocess.Popen(['bash']+args_list, \
                                             #close_fds=True, \
                                            stderr=subprocess.PIPE,\
                                            stdout=subprocess.PIPE)
            #stdout, stderr = p.communicate()
            #stdout = stdout.decode('UTF-8').splitlines()
            #stderr = stderr.decode('UTF-8').splitlines()
            retcode = p.wait()
        except:
            # ERROR
            return True
        
        # Parse the result
        hasfail = False
        hasfail |= (retcode != 0)

        os.chdir(cwd)
        return hasfail
    # ERROR
    return True
#~ def dev_test_runner()

def build_func(repo_root_dir, exe_rel_paths, compiler, flags, clean, reconfigure):
    failed_build = -1 # TODO: get it from Repo manager

    cwd = os.getcwd()
    os.chdir(repo_root_dir)
    try:
        tmp_env = os.environ
        if compiler is not None:
            tmp_env["CC"] = compiler
        if flags is not None:
            tmp_env["CFLAGS"] = flags
        args_list = []
        if clean or reconfigure:
            args_list.append('clean')
        p = subprocess.Popen(['make']+args_list, env=my_env,\
                                            stderr=subprocess.PIPE,\
                                            stdout=subprocess.PIPE)
        retcode = p.wait()
    except:
        return failed_build
    os.chdir(cwd)

    if retcode != 0:
        stdout, stderr = p.communicate()
        stdout = stdout.decode('UTF-8').splitlines()
        stderr = stderr.decode('UTF-8').splitlines()
        print(stdout)
        print(stderr)
        return failed_build 

    return True
#~ def build_func()

### 

PROGRAMMING_LANGUAGE='C'
REPOSITORY_ROOT_DIR=os.path.join(os.path.dirname(this_dir), 'repo')
OUTPUT_ROOT_DIR=os.path.join(os.path.dirname(this_dir), 'ctrl', "output")
RUN_MODE=SessionMode.EXECUTE_MODE

TARGET_SOURCE_INTERMEDIATE_CODE_MAP = {'lib/lib.c':'lib/lib.o', 'main.c':'main.o'}
REPO_EXECUTABLE_RELATIVE_PATHS = ['main']
CODE_BUILDER_FUNCTION = build_func

CUSTOM_DEV_TEST_RUNNER_FUNCTION = dev_test_runner
DEVELOPER_TESTS_LIST = devtestlist

TESTCASE_TOOLS_CONFIGS = [
        TestcaseToolsConfig(tooltype=TestToolType.USE_ONLY_CODE, toolname='custom_devtests', config_id=0),
]

ENABLED_CRITERIA = [
        TestCriteria.STATEMENT_COVERAGE, 
        TestCriteria.BRANCH_COVERAGE,
        TestCriteria.FUNCTION_COVERAGE,
]

gnucov = CriteriaToolsConfig(tooltype=CriteriaToolType.USE_ONLY_CODE, toolname='gcov', config_id=0)
CRITERIA_TOOLS_CONFIGS_BY_CRITERIA = {crit: [gnucov] for crit in ENABLED_CRITERIA} 