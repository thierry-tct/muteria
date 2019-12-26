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
    :param str repo_executables_relpaths: relative path to the executable
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
                                    repo_executables_relpaths, \
                                    source_files_list, \
                                    dev_tests_list)
    
    TODO: IMPORTANT BEFORE ANY PARALLELISM: make sure to avoid deadlock
        and release the lock when there is failure (call to error_exit).
        Implement tools with subprocess for parallelism so as to kill all the 
        subprocess upon error_exit, or continue until join.
"""


from __future__ import print_function

import os
import shutil
import logging
import threading

# https://gitpython.readthedocs.io/en/stable/
from git import Repo as git_repo
import git.exc as git_exc
logging.getLogger("git.cmd").setLevel(logging.INFO)

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

ERROR_HANDLER = common_mix.ErrorHandler

class RepositoryManager(object):
    DEFAULT_TESTS_BRANCH_NAME = "_tests_tmp_muteria_"
    DEFAULT_MUTERIA_REPO_META_FOLDER = ".muteria" 
    def __init__(self, repository_rootdir, repo_executables_relpaths=None, \
                        dev_test_runner_func=None, code_builder_func=None, \
                        dev_test_program_wrapper=None, \
                        source_files_to_objects=None, dev_tests_list=None, \
                        delete_created_on_revert_as_initial=False, \
                        test_branch_name=DEFAULT_TESTS_BRANCH_NAME):
        self.repository_rootdir = repository_rootdir
        self.repo_executables_relpaths = repo_executables_relpaths
        self.dev_test_runner_func = dev_test_runner_func
        self.code_builder_func = code_builder_func
        self.source_files_to_objects = source_files_to_objects
        self.dev_tests_list = dev_tests_list
        self.dev_test_program_wrapper = dev_test_program_wrapper
        if self.dev_test_program_wrapper is not None:
            self.dev_test_program_wrapper = self.dev_test_program_wrapper(self)

        self.delete_created_on_revert_as_initial = \
                                        delete_created_on_revert_as_initial
        self.test_branch_name = test_branch_name

        if self.repo_executables_relpaths is None:
            self.repo_executables_relpaths = []
        if self.dev_tests_list is None:
            self.dev_tests_list = []
        if self.source_files_to_objects is None:
            self.source_files_to_objects = {}

        self.source_files_list = list(self.source_files_to_objects.keys())

        if self.repository_rootdir is None:
            ERROR_HANDLER.error_exit(\
                                "repository rootdir cannot be None", __file__)
        #if self.repo_executables_relpaths is None:
        #    ERROR_HANDLER.error_exit(\
        #                    "repo executable relpath cannot be None", __file__)

        # TODO: Implement a mechanism to avoid deadlock (multiple levels of
        # parallelism)
        self.lock = threading.RLock()

        self.muteria_metadir = os.path.join(self.repository_rootdir, \
                                        self.DEFAULT_MUTERIA_REPO_META_FOLDER)
        self.muteria_metadir_info_file = os.path.join(self.muteria_metadir, \
                                                            "src_infos.json")

        # setup the repo (Should remain as last intruction of initialization)
        self._setup_repository()
    #~ def __init__()

    def get_dev_tests_list(self):
        return self.dev_tests_list
    #~ def get_dev_tests_list()

    def has_dev_tests(self):
        return (self.dev_test_runner_func is not None and \
                                            self.dev_tests_list is not None)
    #~ def has_dev_tests()

    def get_wrapper_object(self):
        return self.dev_test_program_wrapper
    #~ def get_wrapper_object()

    def should_build(self):
        return (self.code_builder_func is not None)
    #~ def should_build()

    def _set_callback_basics(self, callback_object):
        if callback_object is not None:
            callback_object.set_repository_rootdir(self.repository_rootdir)
            callback_object.set_repo_executables_relpaths(\
                                             self.repo_executables_relpaths)
            callback_object.set_source_files_to_objects(\
                                                self.source_files_to_objects)
            callback_object.set_dev_tests_list(self.dev_tests_list)
    #~ def _set_callback_basics()

    def run_dev_test(self, dev_test_name, exe_path_map=None, env_vars=None,\
                    timeout=None, collected_output=None, callback_object=None):
        if self.dev_test_runner_func is None:
            ERROR_HANDLER.error_exit(\
                    "dev_test_runner_func cannot be none when called", \
                                                                    __file__)

        pre_ret = common_mix.GlobalConstants.COMMAND_SUCCESS
        post_ret = common_mix.GlobalConstants.COMMAND_UNCERTAIN
        ret = common_mix.GlobalConstants.COMMAND_UNCERTAIN

        self._set_callback_basics(callback_object)

        self.lock.acquire()
        try:
            if callback_object is not None:
                pre_ret = callback_object.before_command()
            if pre_ret == common_mix.GlobalConstants.COMMAND_SUCCESS:
                ret = self.dev_test_runner_func(dev_test_name, \
                                        self.repository_rootdir, \
                                        exe_path_map=exe_path_map, \
                                        env_vars=(env_vars 
                                                    if env_vars is not None \
                                                    else {}), \
                                        timeout=timeout, \
                                        collected_output=collected_output, \
                                        using_wrapper=(\
                                                    self.get_wrapper_object() \
                                                                is not None))
                                        #self.repo_executables_relpaths)
                if callback_object is not None:
                    callback_object.set_op_retval(ret)
                    post_ret = callback_object.after_command()
        finally:
            self.lock.release()                                
        return (pre_ret, ret, post_ret)
    #~ def run_dev_test()

    def build_code(self, compiler=None, flags_list=None, clean_tmp=False, \
                        reconfigure=False, callback_object=None):
        """ Build the code in repository dir to obtain the executable
        
        :type compiler: str
        :param compiler: name of the compiler to usei. default to None.

        :type flags_list: list
        :param flags_list: list of strings to use as compiler flags. 
                        default to None.

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
            ERROR_HANDLER.error_exit(\
                    "code_builder_func cannot be none when called", __file__)

        pre_ret = common_mix.GlobalConstants.COMMAND_SUCCESS
        post_ret = common_mix.GlobalConstants.COMMAND_UNCERTAIN
        ret = common_mix.GlobalConstants.COMMAND_UNCERTAIN

        self._set_callback_basics(callback_object)

        self.lock.acquire()
        try:
            if callback_object is not None:
                pre_ret = callback_object.before_command()
            if pre_ret == common_mix.GlobalConstants.COMMAND_SUCCESS:
                ret = self.code_builder_func(self.repository_rootdir, \
                                        self.repo_executables_relpaths, \
                                        compiler, flags_list, clean_tmp, \
                                        reconfigure)
                if callback_object is not None:
                    callback_object.set_op_retval(ret)
                    post_ret = callback_object.after_command()
        finally:
            self.lock.release()                                
        return (pre_ret, ret, post_ret)
    #~ def build_code()

    def custom_read_access(self, callback_object):
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

        self.revert_src_list_files()
        
        self._set_callback_basics(callback_object)

        self.lock.acquire()
        try:
            if callback_object is None:
                ERROR_HANDLER.error_exit("{} {}".format(\
                        "callback object must", \
                        "not be None in custom_read_access call"), __file__)
            post_ret = common_mix.GlobalConstants.COMMAND_UNCERTAIN
            pre_ret = callback_object.before_command()
            if pre_ret == common_mix.GlobalConstants.COMMAND_SUCCESS:
                callback_object.set_op_retval(pre_ret)
                post_ret = callback_object.after_command()
        finally:
            self.lock.release()                                
        return (pre_ret, post_ret)
    #~ def custom_read_access()

    def get_repository_dir_path(self):
        return self.repository_rootdir
    #~ def get_repository_dir_path()

    def repo_abs_path(self, relpath):
        return os.path.join(self.repository_rootdir, relpath)
    #~ def repo_abs_path()

    def get_relative_exe_path_map(self):
        exes = list(self.repo_executables_relpaths)
        src_obj_map = dict(self.source_files_to_objects)
        return exes, src_obj_map
    #~ def get_relative_exe_path_map()

    def get_exe_path_map(self):
        exes = [self.repo_abs_path(e) for e in self.repo_executables_relpaths]
        src_obj_map = {}
        for src, dest in list(self.source_files_to_objects.items()):
            src_obj_map[self.repo_abs_path(src)] = \
                            dest if dest is None else self.repo_abs_path(dest)
        return exes, src_obj_map
    #~ def get_exe_path_map()

    def _unlocked_revert_repository_file (self, file_rel_path, gitobj=None):
        if gitobj is None:
            repo = git_repo(self.repository_rootdir)
            gitobj = repo.git
        try:    
            gitobj.checkout('--', file_rel_path)
        except OSError as e:
            ERROR_HANDLER.error_exit("git checkout command " + \
                                    "(-- {}) failed ".format(file_rel_path) + \
                                    "with error: {}".format(str(e)), __file__)
    #~ def _unlocked_revert_repository_file()

    def revert_repository_file (self, file_rel_path, gitobj=None):
        self.lock.acquire()
        try:
            self._unlocked_revert_repository_file(file_rel_path, gitobj)
        finally:
            self.lock.release()                                
    #~ def revert_repository_file()

    def revert_src_list_files (self):
        self.lock.acquire()
        try:
            repo = git_repo(self.repository_rootdir)
            gitobj = repo.git
            #for src in self.source_files_list:
            #    self._unlocked_revert_repository_file(src, gitobj=gitobj)
            self._unlocked_revert_repository_file(self.source_files_list, \
                                                                gitobj=gitobj)
        finally:
            self.lock.release()                                
    #~ def revert_src_list_files()

    def revert_repository(self, as_initial=False):
        #repo = git_repo(self.repository_rootdir)
        #gitobj = repo.git
        self.lock.acquire()
        try:
            if as_initial:
                if self.delete_created_on_revert_as_initial:
                    self._delete_testing_branch(self.repository_rootdir, \
                                                self.test_branch_name)
                else:
                    self.lock.release()                                
                    ERROR_HANDLER.error_exit("{} {}".format(\
                            "revert_repository called with", \
                            "'delete_created_on_revert_as_initial' disabled"),\
                                                                    __file__)
            else:
                # Reset the files but do not delete created files and dir
                self.revert_src_list_files()
                shutil.rmtree(self.muteria_metadir)
                #gitobj.reset('--hard') 
        finally:
            self.lock.release()                                
    #~ def revert_repository()

    def _setup_repository(self):
        # Make sure the repo dir exists
        ERROR_HANDLER.assert_true(os.path.isdir(self.repository_rootdir), \
                        "given repository dir is not existing: {}". format( \
                            self.repository_rootdir), __file__)
        
        # make sure the repo dir is a git repo
        # if no, ask the user whether to initialize and initialize or abort
        # if yes or user accepted initialize, get the git object for the repo
        try:
            repo = git_repo(self.repository_rootdir)
            gitobj = repo.git
        except git_exc.InvalidGitRepositoryError:
            make_it_git = common_mix.confirm_execution("{} {} {} {}".format(\
                                    "The given repository directory is not", \
                                    "a git repository, this must be a git", \
                                    "repository to proceed.\n Do you want to",\
                                    "set is as git repository?"))
            if make_it_git:
                repo = git_repo.init(self.repository_rootdir)
                gitobj = repo.git
            else:
                ERROR_HANDLER.error_exit("{} {}".format(\
                            "Must make the repository as git repository,", \
                            "then re-run"), __file__)

        # Check whether the repo is already managed by muteria
        ## if using branch
        if self.delete_created_on_revert_as_initial:
            if self.test_branch_name not in self._get_branches_list(\
                                                self.repository_rootdir):
                ## Not managed, create branch
                self._make_testing_branch(self.repository_rootdir, \
                                                        self.test_branch_name)

            # checkout
            gitobj.checkout(self.test_branch_name)
        
        # Actual Check whether the repo is already managed by muteria
        # There must be a directory DEFAULT_MUTERIA_REPO_META_FOLDER  
        src_in_prev = set()
        if os.path.isdir(self.muteria_metadir):
            ## Managed
            prev_src_list, prev_use_branch = \
                            common_fs.loadJSON(self.muteria_metadir_info_file)
            ERROR_HANDLER.assert_true(prev_use_branch == \
                        self.delete_created_on_revert_as_initial, \
                        "{} {} {} {} {}".format(\
                            "unmatching repo backup type.", \
                            "previously, use branch was", \
                            prev_use_branch, ", now it is",\
                            self.delete_created_on_revert_as_initial), \
                                                                    __file__)
            src_in_prev = set(prev_src_list) & set(self.source_files_list)
            prev_src_list = set(prev_src_list) - set(self.source_files_list)
            remain_prev_src_set = {src for src in prev_src_list \
                                    if os.path.isfile(self.repo_abs_path(src))}
            # make sure that all prev_src are in initial state
            untracked_diff_files = self._get_untracked_and_diffed(repo)
            prev_untracked_diff = remain_prev_src_set & untracked_diff_files
            if len(prev_untracked_diff) > 0:
                bypass = common_mix.confirm_execution(\
                            "{} {} {} {} {}".format(
                                "the following files were previously used as",\
                                "src files by muteria and are now untracked:",\
                                prev_untracked_diff, \
                                "\nDo you want to handle it or bypass it?",\
                                "Choose yes to bypass: "))
                if not bypass:
                    revert_them = common_mix.confirm_execution(\
                            "{} {}".format(\
                                "Do you want to automatically restore the",\
                                "The untracked previous source and continue?"))
                    if revert_them:
                        for src in prev_untracked_diff:
                            self.revert_repository_file(src, gitobj=gitobj)
                    else:
                        ERROR_HANDLER.error_exit(\
                                "Handle it manually and restart the execution")

            # update the info_file
            if set(prev_src_list) != set(self.source_files_list):
                common_fs.dumpJSON([self.source_files_list, \
                                    self.delete_created_on_revert_as_initial],\
                                                self.muteria_metadir_info_file)
        else:
            ## Not managed
            os.mkdir(self.muteria_metadir)
            common_fs.dumpJSON([self.source_files_list, \
                                    self.delete_created_on_revert_as_initial],\
                                                self.muteria_metadir_info_file)

        # Make sure all source files of interest are tracked
        untracked_diff_files = self._get_untracked_and_diffed(repo)
        untracked_diff_src_in_prev = untracked_diff_files & src_in_prev
        if len(untracked_diff_src_in_prev) > 0:
            if common_mix.confirm_execution(\
                            "{} {} {} {} {}".format("The following source",\
                                        "files of interest are untracked", \
                    "and will be reverted (previous execution unfinished):", \
                                        src_in_prev, \
                                        "do you want to revert them?")):
                for src in src_in_prev:
                    self.revert_repository_file(src, gitobj=gitobj)
            else:
                ERROR_HANDLER.error_exit("{} {}".format(\
                                    "Handle untracked source files manually", \
                                                "then restart the execution"))

        untracked_diff_files = self._get_untracked_and_diffed(repo)
        untracked_diff_src_files = set(self.source_files_list) & \
                                                        untracked_diff_files
        if len(untracked_diff_src_files) > 0:
            if common_mix.confirm_execution(\
                                "{} {} {} {}".format("The following source",\
                                        "files of interest are untracked:", \
                                        untracked_diff_src_files, \
                                        "do you want to track them?")):
                repo.index.add(list(untracked_diff_src_files))
            else:
                ERROR_HANDLER.error_exit("{} {}".format(\
                                    "Handle untracked source files manually", \
                                                "then restart the execution"))

    #~ _setup_repository()

    def _get_untracked_and_diffed(self, repo_):
        try:
            untracked_file_list = repo_.untracked_files
        except UnicodeDecodeError:
            # XXX: error in git python
            non_unicode_files = []
            non_unicode_dirs = []

            def has_unicode_error(name):
                try:
                    name.encode('ascii').decode('unicode_escape')\
                                                            .encode('latin1')
                    return False
                except UnicodeDecodeError:
                    return True
            #~ def has_unicode_error()

            for root_, dirs_, files_ in os.walk(repo_.working_tree_dir):
                for sub_d in dirs_:
                    sd_path = os.path.join(root_, sub_d)
                    if has_unicode_error(sd_path):
                        non_unicode_dirs.append(sd_path)
                for f_ in files_:
                    f_path = os.path.join(root_, f_)
                    if has_unicode_error(f_path):
                        non_unicode_files.append(f_path)
            if common_mix.confirm_execution("Do you want to delete non "
                                            "unicode files and dirs?"):
                # XXX: delete non unicode files
                for d in non_unicode_dirs:
                    if os.path.isdir(d):
                        try:
                            shutil.rmtree(d)
                        except PermissionError:
                            # TODO: avoid using os.system here
                            os.system('sudo rm -rf {}'.format(d))
                for f in non_unicode_files:
                    if os.path.isfile(f):
                        try:
                            os.remove(f)
                        except PermissionError:
                            # TODO: avoid using os.system here
                            os.system('sudo rm -f {}'.format(f))
            else:
                ERROR_HANDLER.error_exit("Non unicode file name of untracked "
                            "files in the repo. Fix it and rerun", __file__)
            untracked_file_list = repo_.untracked_files
        res = set(untracked_file_list) | set(self._get_diffed(repo_))
        return res
    #~ def _get_untracked_and_diffed()

    def _get_diffed (self, repo_):
        res = {}
        d_ind = repo_.index.diff(None)
        for change_type in d_ind.change_type:
            for d in d_ind.iter_change_type(change_type):
                res[d.b_path] = d.change_type
        return res
    #~ def _get_diffed ()

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
