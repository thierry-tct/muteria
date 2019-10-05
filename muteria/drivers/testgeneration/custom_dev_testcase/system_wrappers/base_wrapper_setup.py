
from __future__ import print_function

import os
import sys
import shutil
import logging

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

'''
class SystemNoWrapper(object):
    def cleanup_logs(self, repo_exe_abs_path):
        pass
    def install_wrapper(self, repo_exe_abs_path, run_exe_abs_path, timeout):
        pass
    def uninstall_wrapper(self, repo_exe_abs_path):
        pass
#~ class NoWrapper
'''

class BaseSystemWrapper(object):
    wrapper_template_filename = None #"MUTERIA_WRAPPER.sh.in"
    wrapper_template_string = None 
    
    backup_ext = '.muteria_bak'
    used_ext = '.muteria_used'

    counter_ext = '.muteria_counter'

    outlog_ext = '.muteria_outlog'
    outretcode_ext = '.muteria_outretcode'

    dev_null = None

    def __init__(self, repo_mgr):
        self.repo_mgr = repo_mgr
    #~ def __init__()

    def _get_wrapper_template_path(self):
        return os.path.join(os.path.dirname(__file__), \
                                                self.wrapper_template_filename)
    #~ def _get_wrapper_template_path()

    def _get_repo_run_path_pairs(self, exe_path_map):
        ERROR_HANDLER.assert_true(len(exe_path_map) == 1, \
                                "support a single exe for now", __file__)
        repo_exe = list(exe_path_map.keys())[0]
        run_exe = exe_path_map[repo_exe]
        repo_exe = self.repo_mgr.repo_abs_path(repo_exe)
        if run_exe is None:
            run_exe = repo_exe
        return [(repo_exe, run_exe)]
    #~ def _get_repo_run_path_pairs()

    def cleanup_logs(self, exe_path_map):
        repo_exe_abs_path, _ = self._get_repo_run_path_pairs(exe_path_map)[0]
        if os.path.isfile(repo_exe_abs_path + self.counter_ext):
            os.remove(repo_exe_abs_path + self.counter_ext)
        if os.path.isfile(repo_exe_abs_path + self.outretcode_ext):
            os.remove(repo_exe_abs_path + self.outretcode_ext)
        if os.path.isfile(repo_exe_abs_path + self.outlog_ext):
            os.remove(repo_exe_abs_path + self.outlog_ext)
    #~ def cleanup(repo_exe_abs_path):

    def collect_output(self, exe_path_map, collected_output, testcase):
        repo_exe_abs_path, _ = self._get_repo_run_path_pairs(exe_path_map)[0]
        tmp = []
        if not os.path.isfile(repo_exe_abs_path + self.outretcode_ext):
            ERROR_HANDLER.error_exit("testcase has no log:" + testcase, \
                                                                    __file__)
        with open(repo_exe_abs_path + self.outretcode_ext) as f:
            for line in f:
                tmp.append(line.strip)
            if len(tmp) == 1:
                tmp = tmp[0]
        collected_output.append(tmp)

        with open(repo_exe_abs_path + self.outlog_ext) as f:
            collected_output.append(f.read())
    #~ def collect_output()

    def install_wrapper(self, exe_path_map, timeout, collect_output):
        repo_exe_abs_path, run_exe_abs_path = \
                                self._get_repo_run_path_pairs(exe_path_map)[0]

        # set run exe
        shutil.copy2(run_exe_abs_path, repo_exe_abs_path + self.used_ext)

        # backup
        shutil.move(repo_exe_abs_path, repo_exe_abs_path + self.backup_ext)

        # place the wrapper
        match_replacing = {
            'WRAPPER_TEMPLATE_RUN_EXE_ASBSOLUTE_PATH': \
                                            repo_exe_abs_path+self.used_ext,
            'WRAPPER_TEMPLATE_TIMEOUT': str(timeout),
            'WRAPPER_TEMPLATE_COUNTER_FILE': \
                                        repo_exe_abs_path+self.counter_ext \
                                        if collect_output else self.dev_null,
            'WRAPPER_TEMPLATE_OUTPUT_RETCODE': \
                                        repo_exe_abs_path+self.outretcode_ext \
                                        if collect_output else self.dev_null,
            'WRAPPER_TEMPLATE_OUTPUT_LOG': repo_exe_abs_path+self.outlog_ext,
        }
        if self.wrapper_template_string is None:
            with open(self._get_wrapper_template_path()) as template:
                self.wrapper_template_string = template.read()
        wrapper_obj = self.wrapper_template_string
        for match, replace in match_replacing.items():
            wrapper_obj = wrapper_obj.replace(match, replace)
        with open(repo_exe_abs_path, 'w') as dest:
            dest.write(wrapper_obj+'\n')

        # make executable
        shutil.copymode(repo_exe_abs_path + self.backup_ext, repo_exe_abs_path)

        # cleanup data
        self.cleanup_logs(repo_exe_abs_path)
    #~ def install_wrapper()

    def uninstall_wrapper(self, exe_path_map):
        repo_exe_abs_path, _ = self._get_repo_run_path_pairs(exe_path_map)[0]

        # unset run exe
        shutil.move(repo_exe_abs_path + self.backup_ext, repo_exe_abs_path)

        # small cleanup
        os.remove(repo_exe_abs_path + self.used_ext)

        # cleanup data
        self.cleanup_logs(repo_exe_abs_path)
    #~ def uninstall_wrapper()
#~ class BaseSystemWrapper
