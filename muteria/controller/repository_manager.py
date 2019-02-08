""" This module implememts the class `RepositoryManager` which manages 
    all the access to the project repository.
    An important use of the class is to avoid races during 
    parallel processing. This also implements methods to keep track
    of the changes made to the repository during executions: 
    (the repository is backed before any execution and can be restored after)

    Each method that manipulate the repository, except backing up and
    restoring, take an optional callback function as last argument, which
    will be called after locking the repository, with the last parameters:
        - repository root dir 
        - executable relative path w.r.t the repository root dir
        - list of source files of interest 
                            (as relative path from repository root dir)
        - list of developer test cases of interest

    Callbacks signature:
    :param op_retval: value return by the operation before the callback. 
        None is the value if no operation occured 
        (ex: `RepositoriManager.custom_access`)
    :param callback_args: data object as understandable by the callback.
        The same data is passed to the method of `RepositoryManager` that 
        call the call back. it is then passed to the 
        callback without any change.
    :param str repository_rootdir: full path to the repository root
    :param str repo_executable_relpath: relative path to the executable
        w.r.t the repository root dir
    :param list source_files_list: list of source files we care about.
        each item of the list is a relative path to a source file w.r.t. 
        the repository root dir
    :param list dev_tests_list: list of developer tests we care about.
        each item of the list is a relative path to a test file w.r.t. 
        the repository root dir. 
    :return: The returned value is the returned value of the operation 
        before the call back (in case the callback function is None), or
        the returned value of the callback function.
    >>> def post_process_callback(op_retval, callback_args,\
                                    repository_rootdir, \
                                    repo_executable_relpath, \
                                    source_files_list, \
                                    dev_tests_list)
"""


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
                        dev_test_runner_func, code_builder_func, \
                        source_files_list, dev_tests_list):
        self.repository_rootdir = repository_rootdir
        self.repo_executable_relpath = repo_executable_relpath
        self.dev_test_runner_func = dev_test_runner_func
        self.code_builder_func = code_builder_func
        self.source_files_list = source_files_list
        self.dev_tests_list = dev_tests_list

        if self.repository_rootdir is None:
            logging.error("repository rootdir cannot be none")
            ERROR_HANDLER.error_exit_file(__file__)
        if self.repo_executable_relpath is None:
            logging.error("repo executable relpath cannot be none")
            ERROR_HANDLER.error_exit_file(__file__)

        self.lock = threading.Lock()
    #~ def __init__()

    def run_dev_test(self, dev_test_name, post_process_callback=None, \
                                            callback_args=None):
        if self.dev_test_runner_func is None:
            logging.error("dev_test_runner_func cannot be none when called")
            ERROR_HANDLER.error_exit_file(__file__)
        self.lock.acquire()
        try:
            ret = self.dev_test_runner_func(dev_test_name, \
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath)
            if post_process_callback is not None:
                ret = post_process_callback(ret, callback_args,\
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath, \
                                        self.source_files_list, \
                                        self.dev_tests_list)
        finally:
            self.lock.release()                                
        return ret
    #~ def run_dev_test()

    def build_code(self, compiler=None, flags=None, clean_tmp=False, \
                        reconfigure=False, post_process_callback=None, \
                        callback_args=None):
        """ Build the code in repository dir to obtain the executable
        
        :type compiler: str
        :param compiler: name of the compiler to usei. default to None.

        :type flags: str
        :param flags: string to use as compiler flags. default to None.

        :type clean_tmp: bool
        :param clean_tmp: enable clean any build temporary files, 
                such as object files in C/C++ . Default to False.

        :type \reconfigure: bool
        :param \reconfigure: enable reconfigure the project repository before
                building. may be usefule if using a different compiler
                on different runs. default to False.

        :type post_process_callback: funtion
        :param post_process_callback: function that will be called after
                the code is build. The call pass first the returned
                value of the build (True is succeed, False if failed).
                the second argument is the `callback_args` passed 
                to the function. the remaining four arguments are the
                project element (repos rootdir absolute path, 
                executable relative path, list of source files,
                list of developer tests). Default to None.

        :type \callback_args: anything
        :param \callback_args: data that will be passed (untouched) to the
                callback function `post_process_callback`. Default to None.

        :raises: Terminates execution with error if the specified
                `self.code_builder_func` is None.

        :rtype: bool if `post_process_callback` is None, the returned value 
                is True if build succeed, False otherwise. The returned
                value is the returned value of `post_process_callback`
                 `post_process_callback` is not None.
                    
        """

        if self.code_builder_func is None:
            logging.error("code_builder_func cannot be none when called")
            ERROR_HANDLER.error_exit_file(__file__)
        self.lock.acquire()
        try:
            ret = self.code_builder_func(self.repository_rootdir, \
                                    self.repo_executable_relpath, \
                                    compiler, flags, clean_tmp, reconfigure)
            if post_process_callback is not None:
                ret = post_process_callback(ret, callback_args, \
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath, \
                                        self.source_files_list, \
                                        self.dev_tests_list)
        finally:
            self.lock.release()                                
        return ret
    #~ def build_code()

    def custom_access(self, post_process_callback, callback_args=None):
        """ Execute the callback function and return its returned value
        TODO: Complete the doc
        :type post_process_callback:
        :param post_process_callback:

        :type callback_args:
        :param callback_args:

        :raises:

        :rtype:
        """

        self.lock.acquire()
        try:
            ret = None
            if post_process_callback is not None:
                ret = post_process_callback(ret, callback_args, \
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath, \
                                        self.source_files_list, \
                                        self.dev_tests_list)
        finally:
            self.lock.release()                                
        return ret
    #~ def custom_access()

    def revert_repository(self, as_initial=False):
        #TODO: delete the branch is as_initial is true
        # Only revert the files to initial otherwise
    #~ def revert_repository()

    def setup_repository(self):
        #TODO : create git repos if not. Use git branch
    #~ setup repository()
#~ class RepositoryManager