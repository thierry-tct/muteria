import os
from muteria.common.mix import GlobalConstants
from muteria.drivers import DriversUtils

def bash_test_runner(test_name, repo_root_dir, exe_path_map, env_vars, \
                                            timeout, collected_output=None):
    # TODO: use exe_path_map

    cwd = os.getcwd()
    os.chdir(repo_root_dir)

    # TODO: pass the test script name as env_var to wrapper so that only 
    # TODO: call from that are considered

    try:
        args_list = [test_name]
        if collected_output is None:
            retcode, _, _ = DriversUtils.execute_and_get_retcode_out_err(\
                                prog='bash', args_list=args_list, \
                            timeout=timeout, out_on=False, err_on=False)
        else:
            # collected_output is a list ([retcode, out_err_log])
            # TODO: use wrapper to get the output 
            assert False, "TO BE Implemented"
    except:
        # ERROR
        return GlobalConstants.TEST_EXECUTION_ERROR
    
    # Parse the result
    hasfail = False
    hasfail |= (retcode != 0)

    os.chdir(cwd)
    return GlobalConstants.FAIL_TEST_VERDICT if hasfail else \
                                            GlobalConstants.PASS_TEST_VERDICT
#~ def dev_test_runner()