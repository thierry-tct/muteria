""" Typical approach to bypass doing 'make check TESTS=...' 
    for each individual test.
    
    Get the env vars set by make check TESTS and just pass them when 
    running a test.

    make the test runner call the function 'get_make_check_tests_env_vars'
    in your dev test runner and use it when running the test with
    bash or perl.
"""

import os
import json


make_check_test_env_keys = ["VERSION", "LOCALE_FR", "LOCALE_FR_UTF8", "abs_top_builddir", \
                            "abs_top_srcdir", "abs_srcdir", "built_programs", "host_os", \
                            "host_triplet", "srcdir", "top_srcdir", "CONFIG_HEADER", \
                            #"CU_TEST_NAME", \
                            "CC", "AWK", "EGREP", "EXEEXT", "MAKE", "PACKAGE_VERSION", \
                            "PERL", "PREFERABLY_POSIX_SHELL"] 
make_check_test_env_vars = None


def get_make_check_tests_env_vars(repo_make_check_dir):
    # TCT
    global make_check_test_env_vars
    if make_check_test_env_vars is None:
        # obtain it
        tmp_getenv_hook = os.path.join(repo_make_check_dir, 'my_conf_test_hook.conf.tmp')
        tmp_getenv_hook_sh = tmp_getenv_hook + '.sh'
        tmp_getenv_hook_json = tmp_getenv_hook + '.json'
        with open(tmp_getenv_hook_sh, 'w') as f:
            contain_str = "#! /bin/bash\n\n"
            contain_str += "python -c \"import os; import json; " \
					+ "f = open('{}', 'w'); ".format(tmp_getenv_hook_json) \
					+ "json.dump(dict(os.environ), f); " \
					+ "f.close()\"\n"
            contain_str += "exit $?"
            f.write(contain_str+'\n')
        os.system('chmod +x '+tmp_getenv_hook_sh)
        os.system('make check TESTS='+tmp_getenv_hook_sh)
        assert os.path.isfile(tmp_getenv_hook_json), "Getting makefile runtest env failed."\
					" File {} is missing".format(tmp_getenv_hook_json)
        with open(tmp_getenv_hook_json) as f: 
            make_check_test_env_vars = json.load(f)
        useless_make_test_env_keys = set(make_check_test_env_vars) \
										- set(make_check_test_env_keys)
        for k in useless_make_test_env_keys:
            del make_check_test_env_vars[k]
        # TODO: failure error handling
        
        # cleanup
        os.remove(tmp_getenv_hook_sh)
        os.remove(tmp_getenv_hook+'.log')
        os.remove(tmp_getenv_hook+'.trs')
        os.remove(tmp_getenv_hook_json)

    return make_check_test_env_vars
#~ def get_make_check_tests_env_vars()

