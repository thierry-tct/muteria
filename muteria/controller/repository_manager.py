
from __future__ import print_function

import logging
import threading

# https://gitpython.readthedocs.io/en/stable/
from git import Repo as git_repo

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class RepositoryManager(object):
    PASS = 0
    FAIL = 1
    ERROR = -1
    def __init__(self, repository_rootdir, repo_executable_relpath, \
                        dev_test_runner_func, code_builder_func):
        self.repository_rootdir = repository_rootdir
        self.repo_executable_relpath = repo_executable_relpath
        self.dev_test_runner_func = dev_test_runner_func
        self.code_builder_func = code_builder_func

        if self.repository_rootdir is None:
            logging.error("repository rootdir cannot be none")
            ERROR_HANDLER.error_exit_file(__file__)
        if self.repo_executable_relpath is None:
            logging.error("repo executable relpath cannot be none")
            ERROR_HANDLER.error_exit_file(__file__)

        self.lock = threading.Lock()
    #~ def __init__()

    def run_dev_test(self, dev_test_name, post_process_callback=None):
        if self.dev_test_runner_func is None:
            logging.error("dev_test_runner_func cannot be none when called")
            ERROR_HANDLER.error_exit_file(__file__)
        self.lock.acquire()
        try:
            ret = self.dev_test_runner_func(dev_test_name, \
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath)
            if post_process_callback is not None:
                post_process_callback(ret, dev_test_name, \
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath)
        finally:
            self.lock.release()                                
        return ret
    #~ def run_dev_test()

    def build_code(self, compiler=None, flags=None, clean_tmp=False, \
                        reconfigure=False, post_process_callback=None):
        if self.code_builder_func is None:
            logging.error("code_builder_func cannot be none when called")
            ERROR_HANDLER.error_exit_file(__file__)
        self.lock.acquire()
        try:
            ret = self.code_builder_func(self.repository_rootdir, \
                                    self.repo_executable_relpath, \
                                    compiler, flags, clean_tmp, reconfigure)
            if post_process_callback is not None:
                post_process_callback(ret, self.repository_rootdir, \
                                        self.repo_executable_relpath)
        finally:
            self.lock.release()                                
        return ret
    #~ def build_code()

    def revert_repository(self, as_initial=False):
        #TODO: delete the branch is as_initial is true
        # Only revert the files to initial otherwise
    #~ def revert_repository()

    def setup_repository(self):
        #TODO : create git repos if not. Use git branch
    #~ setup repository()
#~ class RepositoryManager