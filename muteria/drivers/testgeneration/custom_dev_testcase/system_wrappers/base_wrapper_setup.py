
from __future__ import print_function

import os
import sys
import shutil
import logging
import abc

import muteria.common.mix as common_mix

import muteria.drivers.testgeneration.custom_dev_testcase.system_wrappers as \
                                                                system_wrappers

ERROR_HANDLER = common_mix.ErrorHandler

class BaseSystemTestSplittingWrapper(abc.ABC):
    def get_sub_test_id_env_vars(self, subtest_id):
        return {system_wrappers.TEST_COUNT_ID_ENV_VAR: str(subtest_id)}    
    #~ def get_sub_test_id_env_vars()

    @abc.abstractmethod
    def set_wrapper(self, workdir, exe_path_map):
        """ Return the new exe path map
        """
        print ("Implement!!!")
    #~ def set_wrapper()

    @abc.abstractmethod
    def switch_to_new_test(self):
        """ reset the counters
        """
        print ("Implement!!!")
    #~ def switch_to_new_test()

    @abc.abstractmethod
    def collect_data(self):
        """ get number of sub tests and args
        """
        print ("Implement!!!")
    #~ def collect_data()

    @abc.abstractmethod
    def cleanup(self):
        print ("Implement!!!")
    #~ def cleanup()
#~ class BaseSystemTestSplittingWrapper

class BaseSystemWrapper(abc.ABC):
    
    # do not change

    backup_ext = '.muteria_bak'
    used_ext = '.muteria_used'

    counter_ext = '.muteria_counter'

    outlog_ext = '.muteria_outlog'
    outretcode_ext = '.muteria_outretcode'

    # Must Override

    @abc.abstractmethod
    def get_dev_null(self):
        print ("Implement!!!")
    #~ def get_dev_null()

    @abc.abstractmethod
    def _get_wrapper_template_string(self):
        print("Implement!!!")
    #~ def _get_wrapper_template_string()

    @abc.abstractmethod
    def _get_timedout_codes(self):
        print("Implement!!!")
    #~ def _get_timedout_codes()

    ## Wrapper test splitting TODO TODO
    @abc.abstractmethod
    def get_test_splitting_wrapper_class(self):
        print("Implement!!!")
    #~ def get_sub_test_id_env_vars()

    # Can override

    def __init__(self, repo_mgr):
        self.repo_mgr = repo_mgr
        self.test_splitting_wrapper = self.get_test_splitting_wrapper_class()
        if self.test_splitting_wrapper is not None:
            self.test_splitting_wrapper = self.test_splitting_wrapper()
    #~ def __init__()

    def get_test_splitting_wrapper(self):
        return self.test_splitting_wrapper
    #~ def get_test_splitting_wrapper()

    def _get_repo_run_path_pairs(self, exe_path_map):
        ERROR_HANDLER.assert_true(len(exe_path_map) == 1, \
                    "support a single exe for now. got: "+str(exe_path_map), \
                                                                    __file__)
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
            ERROR_HANDLER.error_exit("testcase has no log: '" +testcase+ "'."
                                " repo_exe_abs_path is " + repo_exe_abs_path, \
                                                                    __file__)
        timedout = []

        with open(repo_exe_abs_path + self.outretcode_ext) as f:
            for line in f:
                tmp.append(int(line.strip()))
                timedout.append(tmp[-1] in self._get_timedout_codes())            
            if len(tmp) == 1:
                tmp = tmp[0]
                timedout = timedout[0]
        collected_output.append(tmp)

        try:
            with open(repo_exe_abs_path + self.outlog_ext) as f:
                collected_output.append(f.read())
        except UnicodeDecodeError:
            with open(repo_exe_abs_path + self.outlog_ext, \
                                                encoding='ISO-8859-1') as f:
                collected_output.append(f.read())

        collected_output.append(timedout) 
    #~ def collect_output()

    def install_wrapper(self, exe_path_map, collect_output):
        repo_exe_abs_path, run_exe_abs_path = \
                                self._get_repo_run_path_pairs(exe_path_map)[0]

        if os.path.isfile(repo_exe_abs_path + self.used_ext):
            os.remove(repo_exe_abs_path + self.used_ext)

        # set run exe
        try:
            shutil.copy2(run_exe_abs_path, repo_exe_abs_path + self.used_ext)
            # use link instead of copy to avoid copying large unchanging exes
            #os.link(run_exe_abs_path, repo_exe_abs_path + self.used_ext)
        except PermissionError:
            os.remove(repo_exe_abs_path + self.used_ext)
            shutil.copy2(run_exe_abs_path, repo_exe_abs_path + self.used_ext)
            # use link instead of copy to avoid copying large unchanging exes
            #os.link(run_exe_abs_path, repo_exe_abs_path + self.used_ext)

        # backup
        shutil.move(repo_exe_abs_path, repo_exe_abs_path + self.backup_ext)

        # place the wrapper
        match_replacing = {
            'WRAPPER_TEMPLATE_DEFAULT_EXE_ASBSOLUTE_PATH': \
                                            repo_exe_abs_path+self.backup_ext,
            'WRAPPER_TEMPLATE_RUN_EXE_ASBSOLUTE_PATH': \
                                            repo_exe_abs_path+self.used_ext,
            'WRAPPER_TEMPLATE_COUNTER_FILE': \
                                        repo_exe_abs_path+self.counter_ext, \
            'WRAPPER_TEMPLATE_OUTPUT_RETCODE': \
                                    repo_exe_abs_path+self.outretcode_ext \
                                    if collect_output else self.get_dev_null(),
            'WRAPPER_TEMPLATE_OUTPUT_LOG': repo_exe_abs_path+self.outlog_ext \
                                    if collect_output else self.get_dev_null(),
        }
        wrapper_obj = self._get_wrapper_template_string()
        for match, replace in match_replacing.items():
            wrapper_obj = wrapper_obj.replace(match, replace)
        with open(repo_exe_abs_path, 'w') as dest:
            dest.write(wrapper_obj+'\n')

        # make executable
        shutil.copymode(repo_exe_abs_path + self.backup_ext, repo_exe_abs_path)

        # cleanup data
        self.cleanup_logs(exe_path_map)
    #~ def install_wrapper()

    def uninstall_wrapper(self, exe_path_map):
        repo_exe_abs_path, _ = self._get_repo_run_path_pairs(exe_path_map)[0]

        # unset run exe
        shutil.move(repo_exe_abs_path + self.backup_ext, repo_exe_abs_path)

        # small cleanup
        if os.path.isfile(repo_exe_abs_path + self.used_ext):
            os.remove(repo_exe_abs_path + self.used_ext)

        # cleanup data
        self.cleanup_logs(exe_path_map)
    #~ def uninstall_wrapper()
#~ class BaseSystemWrapper
