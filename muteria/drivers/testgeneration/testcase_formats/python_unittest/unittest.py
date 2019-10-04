import os
import sys
from muteria.common.mix import GlobalConstants
from muteria.drivers import DriversUtils

def python_unittest_runner(test_name, repo_root_dir, exe_path_map, env_vars, \
                                            timeout, collected_output=None):
    # TODO: use exe_path_map 

    def parse_test(s):
        return s.split('...')[0].replace(':','/').replace(' ','')

    cwd = os.getcwd()
    os.chdir(repo_root_dir)

    try:
        args_list = ['-m', 'unittest', test_name, '-v']

        if collected_output is None:
            retcode, stdout, _ = DriversUtils.execute_and_get_retcode_out_err(\
                                prog=sys.executable, args_list=args_list, \
                                        timeout=timeout, merge_err_to_out=True)
            stdout = stdout.splitlines()
        else:
            # collected_output is a list ([retcode, out_err_log])
            # TODO: use wrapper? or parse out for particular codes... 
            assert False, "TO BE Implemented"
    except:
        # ERROR
        os.chdir(cwd)
        return GlobalConstants.TEST_EXECUTION_ERROR
    
    # Parse the result
    subtests_verdicts = {}
    hasfail = False
    hasfail |= (retcode != 0)
    for s in stdout:
        if s.endswith('... FAIL'):
            hasfail = True
            subtests_verdicts[parse_test(s)] = True
        elif s.endswith('... ok'):
            subtests_verdicts[parse_test(s)] = False
    #print(subtests_verdicts)
    os.chdir(cwd)
    return GlobalConstants.FAIL_TEST_VERDICT if hasfail else \
                                            GlobalConstants.PASS_TEST_VERDICT
#~ def python_unittest_runner()