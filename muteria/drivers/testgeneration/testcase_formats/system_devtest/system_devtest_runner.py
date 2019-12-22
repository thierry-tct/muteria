import os
import logging
import shutil

from muteria.common.mix import GlobalConstants
from muteria.drivers import DriversUtils

from muteria.drivers.testgeneration.custom_dev_testcase.system_wrappers \
                import TEST_FILE_NAME_ENV_VAR, TEST_EXECUTION_TIMEOUT_ENV_VAR

def system_test_runner(prog, args_list, test_filename, repo_root_dir, \
                            exe_path_map=None, env_vars=None, timeout=None, \
                            collected_output=None, using_wrapper=False, \
                            dbg_log_execution_out=False):
    try:
        tmp_env = os.environ.copy()
        if env_vars is not None:
            #for e, v in env_vars.items():
            #    tmp_env[e] = v
            tmp_env.update(env_vars)
        if test_filename is not None:
            tmp_env[TEST_FILE_NAME_ENV_VAR] = test_filename
        if using_wrapper and timeout is not None:
            tmp_env[TEST_EXECUTION_TIMEOUT_ENV_VAR] = str(timeout)
            timeout = None

        if collected_output is None:
            retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                prog=prog, args_list=args_list, env=tmp_env,\
                                timeout=timeout, out_on=dbg_log_execution_out,\
                                err_on=dbg_log_execution_out, \
                                merge_err_to_out=True)
        else:
            retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                prog=prog, args_list=args_list, env=tmp_env,\
                                timeout=timeout, merge_err_to_out=True)
            collected_output.append(retcode)
            collected_output.append(out)

        if dbg_log_execution_out:
            logging.debug("(DBG - Test Output):\n"+out)
    except (ValueError, OSError) as e:
        # ERROR
        # TODO: 
        return GlobalConstants.TEST_EXECUTION_ERROR
    
    # Parse the result
    hasfail = False
    hasfail |= (retcode != 0)

    return GlobalConstants.FAIL_TEST_VERDICT if hasfail else \
                                            GlobalConstants.PASS_TEST_VERDICT
#~ def dev_test_runner()
