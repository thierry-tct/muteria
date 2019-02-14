""" This module implememts the class `RepositoryManager` which manages 
    all the access to the project repository.
    An important use of the class is to avoid races during 
    parallel processing. This also implements methods to keep track
    of the changes made to the repository during executions: 
    (the repository is backed before any execution and can be restored after)

    Each method that manipulate the repository, except backing up and
    restoring, take one or two optional callback functions and 
    callback arguments as last arguments 
    (callback function mandatory only for custom_read_access), 
    which will be called after locking the repository, 
    with the last parameters:
        - repository root dir 
        - executable relative path w.r.t the repository root dir
        - list of source files of interest 
                            (as relative path from repository root dir)
        - list of developer test cases of interest

    Callbacks signature:
    :param op_retval: value return by the operation before the callback. 
        None is the value if no operation occured 
        (ex: `RepositorManager.custom_access`)
        Note: this is only present for post processing callbacks
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
    DEFAULT_TESTS_BRANCH_NAME = "_tests_tmp_muteria_"
    def __init__(self, repository_rootdir, repo_executable_relpath, \
                        dev_test_runner_func, code_builder_func, \
                        source_files_list, dev_tests_list, \
                        delete_created_on_revert_as_initial=False, \
                        test_branch_name=DEFAULT_TESTS_BRANCH_NAME):
        self.repository_rootdir = repository_rootdir
        self.repo_executable_relpath = repo_executable_relpath
        self.dev_test_runner_func = dev_test_runner_func
        self.code_builder_func = code_builder_func
        self.source_files_list = source_files_list
        self.dev_tests_list = dev_tests_list

        self.delete_created_on_revert_as_initial = \
                                        delete_created_on_revert_as_initial
        self.test_branch_name = test_branch_name

        if self.repository_rootdir is None:
            logging.error("repository rootdir cannot be none")
            ERROR_HANDLER.error_exit_file(__file__)
        if self.repo_executable_relpath is None:
            logging.error("repo executable relpath cannot be none")
            ERROR_HANDLER.error_exit_file(__file__)

        self.lock = threading.Lock()
    #~ def __init__()

    def run_dev_test(self, dev_test_name, \
                    pre_process_callback=None, pre_callback_args=None, \
                    post_process_callback=None, post_callback_args=None):
        if self.dev_test_runner_func is None:
            logging.error("dev_test_runner_func cannot be none when called")
            ERROR_HANDLER.error_exit_file(__file__)

        pre_ret = True
        post_ret = None

        self.lock.acquire()
        try:
            if pre_process_callback is not None:
                pre_ret = pre_process_callback(pre_callback_args,\
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath, \
                                        self.source_files_list, \
                                        self.dev_tests_list)
            if pre_ret:
                ret = self.dev_test_runner_func(dev_test_name, \
                                            self.repository_rootdir, \
                                            self.repo_executable_relpath)
                if post_process_callback is not None:
                    post_ret = post_process_callback(ret, post_callback_args,\
                                            self.repository_rootdir, \
                                            self.repo_executable_relpath, \
                                            self.source_files_list, \
                                            self.dev_tests_list)
        finally:
            self.lock.release()                                
        return (pre_ret, post_ret)
    #~ def run_dev_test()

    def build_code(self, compiler=None, flags=None, clean_tmp=False, \
                        reconfigure=False, \
                        pre_process_callback=None, pre_callback_args=None, \
                        post_process_callback=None, post_callback_args=None):
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
        :type pre_process_callback: funtion
        :param pre_process_callback: function that will be called before
                the code is build. 
                the first argument is the `pre_callback_args` passed 
                to the function. the remaining four arguments are the
                project element (repos rootdir absolute path, 
                executable relative path, list of source files,
                list of developer tests). Default to None.
                The build script and `post_process_callback` are called
                if and only if this function return True.

        :type pre_callback_args: anything
        :param pre_callback_args: data that will be passed (untouched) to the
                callback function `pre_process_callback`. Default to None.

        :type post_process_callback: funtion
        :param post_process_callback: function that will be called after
                the code is build. The call pass first the returned
                value of the build (True is succeed, False if failed).
                the second argument is the `callback_args` passed 
                to the function. the remaining four arguments are the
                project element (repos rootdir absolute path, 
                executable relative path, list of source files,
                list of developer tests). Default to None.

        :type post_callback_args: anything
        :param post_callback_args: data that will be passed (untouched) to the
                callback function `post_process_callback`. Default to None.

        :raises: Terminates execution with error if the specified
                `self.code_builder_func` is None.

        :rtype: The returned value is the pair of returned value of 
                `pre_process_callback` and `post_process_callback`.
                if `pre_process_callback` is None, the default return is True.
                if `post_process_callback` is None, the default return is None.
        """

        if self.code_builder_func is None:
            logging.error("code_builder_func cannot be none when called")
            ERROR_HANDLER.error_exit_file(__file__)

        pre_ret = True
        post_ret = None

        self.lock.acquire()
        try:
            if pre_process_callback is not None:
                pre_ret = pre_process_callback(pre_callback_args,\
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath, \
                                        self.source_files_list, \
                                        self.dev_tests_list)
            if pre_ret:
                ret = self.code_builder_func(self.repository_rootdir, \
                                        self.repo_executable_relpath, \
                                        compiler, flags, clean_tmp, \
                                        reconfigure)
                if post_process_callback is not None:
                    post_ret = post_process_callback(ret, post_callback_args, \
                                            self.repository_rootdir, \
                                            self.repo_executable_relpath, \
                                            self.source_files_list, \
                                            self.dev_tests_list)
        finally:
            self.lock.release()                                
        return (pre_ret, post_ret)
    #~ def build_code()

    def custom_read_access(self, process_callback, callback_args=None):
        """ Execute the read only callback function and 
            return its returned value
        :type process_callback: function
        :param process_callback: function that will be called after
                the code is build. The call pass first the returned
                value of the build (True is succeed, False if failed).
                the second argument is the `callback_args` passed 
                to the function. the remaining four arguments are the
                project element (repos rootdir absolute path, 
                executable relative path, list of source files,
                list of developer tests). Default to None.

        :type callback_args: anything
        :param callback_args: data that will be passed (untouched) to the
                callback function `process_callback`. Default to None.

        :raises: error if process_callback is None

        :rtype: any
        """

        self.lock.acquire()
        try:
            if process_callback is None:
                logging.error("{} {}".format("process_callback must", \
                                    "not be None in custom_read_access call"))
                ERROR_HANDLER.error_exit_file(__file__)
            ret = process_callback(callback_args, \
                                        self.repository_rootdir, \
                                        self.repo_executable_relpath, \
                                        self.source_files_list, \
                                        self.dev_tests_list)
        finally:
            self.lock.release()                                
        return ret
    #~ def custom_read_access()


    def revert_repository_file (self, file_rel_path):
        repo = git_repo(self.repository_rootdir)
        gitobj = repo.git
        gitobj.checkout('--', file_rel_path)
    #~ def revert_repository_file()

    def revert_src_list_files (self):
        repo = git_repo(self.repository_rootdir)
        gitobj = repo.git
        for src in self.source_files_list:
            gitobj.checkout('--', src)
    #~ def revert_src_list_files()

    def revert_repository(self, as_initial=False):
        repo = git_repo(self.repository_rootdir)
        gitobj = repo.git

        if as_initial:
            if self.delete_created_on_revert_as_initial:
                self._delete_testing_branch(self.repository_rootdir, \
                                            self.test_branch_name)
            else:
                logging.error("{} {}".format("revert_repository called with", \
                            "'delete_created_on_revert_as_initial' disabled"))
                ERROR_HANDLER.error_exit_file(__file__)
        else:
            # Reset the files but do not delete created files and dir
            gitobj.reset('--hard') 
    #~ def revert_repository()

    def setup_repository(self):
        repo = git_repo(self.repository_rootdir)
        gitobj = repo.git

        if self.delete_created_on_revert_as_initial:
            self._make_testing_branch(self.repository_rootdir, \
                                        self.test_branch_name)
            # checkout
            gitobj.checkout(self.test_branch_name)

            #TODO create muteria branch and the muteria metadir 
    #~ setup repository()


    def _make_testing_branch(self, repo_dir, branch_name):
        # create 'test' branch if it doesn't exist 
        # so that it can be used for tests in this module
        clean_branch_list = self._get_branches_list(repo_dir)

        repo = git_repo(repo_dir)
        gitobj = repo.git
        
        if branch_name in clean_branch_list:
            newly_made = False
        else:
            gitobj.branch(branch_name)
            newly_made = True
        return newly_made
    #~ def _make_testing_branch()

    def _delete_testing_branch(self, repo_dir, branch_name):
        clean_branch_list = self._get_branches_list(repo_dir)

        repo = git_repo(repo_dir)
        gitobj = repo.git
        
        just_deleted = False
        if branch_name in clean_branch_list:
            gitobj.branch('-d', branch_name)
            just_deleted = True
        return just_deleted
    #~ def _delete_testing_branch()

    def _get_branches_list(self, repo_dir):
        repo = git_repo(repo_dir)
        gitobj = repo.git

        git_branch_string = gitobj.branch()
        git_branch_list = git_branch_string.split("\n")
        clean_branch_list = []
        for branch in git_branch_list:
            branch = branch.replace('*', '')
            branch = branch.replace(' ', '')
            clean_branch_list.append(branch)
        return clean_branch_list
    #~ def _get_branches_list()
#~ class RepositoryManager