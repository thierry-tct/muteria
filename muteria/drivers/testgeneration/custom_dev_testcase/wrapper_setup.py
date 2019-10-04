
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

def install_wrapper(exe_abs_path, outlog_abs_path, retcode_abs_path, \
                                                        counter_file_abs_path):
    assert False
#~ def install_wrapper()

def uninstall_wrapper(exe_abs_path, outlog_abs_path, retcode_abs_path, \
                                                        counter_file_abs_path):
    assert False
#~ def uninstall_wrapper()