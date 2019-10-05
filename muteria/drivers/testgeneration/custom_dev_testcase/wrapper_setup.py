
from __future__ import print_function

import os
import sys
import shutil
import logging

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

wrapper_template_name = "MUTERIA_WRAPPER.sh.in"
wrapper_template_path = os.path.join(os.path.dirname(__file__), \
                                                        wrapper_template_name)
backup_ext = '.muteria_bak'
used_ext = '.muteria_used'

counter_ext = '.muteria_counter'

outlog_ext = '.muteria_outlog'
outretcode_ext = '.muteria_outretcode'

def cleanup_logs(repo_exe_abs_path):
    if os.path.isfile(repo_exe_abs_path + counter_ext):
        os.remove(repo_exe_abs_path + counter_ext)
    if os.path.isfile(repo_exe_abs_path + outretcode_ext):
        os.remove(repo_exe_abs_path + outretcode_ext)
    if os.path.isfile(repo_exe_abs_path + outlog_ext):
        os.remove(repo_exe_abs_path + outlog_ext)
#~ def cleanup(repo_exe_abs_path):

def install_wrapper(repo_exe_abs_path, run_exe_abs_path, timeout):
    # set run exe
    shutil.copy2(run_exe_abs_path, repo_exe_abs_path + used_ext)

    # backup
    shutil.move(repo_exe_abs_path, repo_exe_abs_path + backup_ext)

    # place the wrapper
    match_replacing = {
        'WRAPPER_TEMPLATE_RUN_EXE_ASBSOLUTE_PATH': repo_exe_abs_path+used_ext,
        'WRAPPER_TEMPLATE_TIMEOUT': str(timeout),
        'WRAPPER_TEMPLATE_COUNTER_FILE': repo_exe_abs_path+counter_ext,
        'WRAPPER_TEMPLATE_OUTPUT_RETCODE': repo_exe_abs_path+outretcode_ext,
        'WRAPPER_TEMPLATE_OUTPUT_LOG': repo_exe_abs_path+outlog_ext,
    }
    with open(wrapper_template_path) as template:
        template_obj = template.read()
    for match, replace in match_replacing.items():
        template_obj = template_obj.replace(match, replace)
    with open(repo_exe_abs_path, 'w') as dest:
        dest.write(template_obj+'\n')

    # make executable
    shutil.copymode(repo_exe_abs_path + backup_ext, repo_exe_abs_path)

    # cleanup data
    cleanup_logs(repo_exe_abs_path)
#~ def install_wrapper()

def uninstall_wrapper(repo_exe_abs_path):
    # unset run exe
    shutil.move(repo_exe_abs_path + backup_ext, repo_exe_abs_path)

    # small cleanup
    os.remove(repo_exe_abs_path + used_ext)

    # cleanup data
    cleanup_logs(repo_exe_abs_path)
#~ def uninstall_wrapper()
