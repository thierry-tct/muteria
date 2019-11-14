
from __future__ import print_function

import os
import shutil
import abc

import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

class BaseCallbackObject(abc.ABC):
    def __init__(self, op_retval=None, pre_callback_args=None, \
                                post_callback_args=None, \
                                repository_rootdir=None, \
                                repo_executables_relpaths=None, \
                                source_files_to_objects=None, \
                                dev_tests_list=None):
        self.op_retval = op_retval
        self.pre_callback_args = pre_callback_args
        self.post_callback_args = post_callback_args
        self.repository_rootdir = repository_rootdir
        self.repo_executables_relpaths = repo_executables_relpaths
        self.source_files_to_objects = source_files_to_objects
        self.dev_tests_list = dev_tests_list
    #~ def __init__()

    def _copy_from_repo(self, file_src_dest_map, skip_none_dest=False):
        for src, dest in list(file_src_dest_map.items()):
            if dest is None:
                if skip_none_dest: 
                    continue
                ERROR_HANDLER.error_exit("dest is None while not skipped", \
                                                                    __file__)
            abs_src = os.path.join(self.repository_rootdir, src)
            if os.path.abspath(abs_src) == os.path.abspath(dest):
                ERROR_HANDLER.error_exit("src and dest are same (from repo)", \
                                                                    __file__)
            try:
                shutil.copy2(abs_src, dest)
            except PermissionError:
                os.remove(dest)
                shutil.copy2(abs_src, dest)
    #~ def _copy_from_repo()

    def _copy_to_repo(self, file_src_dest_map, skip_none_dest=False):
        for src, dest in list(file_src_dest_map.items()):
            if dest is None:
                if skip_none_dest: 
                    continue
                ERROR_HANDLER.error_exit("dest is None while not skipped", \
                                                                    __file__)
            abs_src = os.path.join(self.repository_rootdir, src)
            if os.path.abspath(abs_src) == os.path.abspath(dest):
                ERROR_HANDLER.error_exit("src and dest are same (to repo)", \
                                                                    __file__)

            abs_src_stat = None
            if os.path.isfile(abs_src):
                abs_src_stat = os.stat(abs_src)

            try:
                shutil.copy2(dest, abs_src)
            except PermissionError:
                os.remove(abs_src)
                shutil.copy2(dest, abs_src)

            if abs_src_stat is not None:
                os.utime(abs_src, \
                              (abs_src_stat.st_atime, abs_src_stat.st_mtime))
    #~ def _copy_from_repo()

    def set_op_retval(self, op_retval):
        self.op_retval = op_retval
    #~ def set_op_retval()
    
    def set_repository_rootdir(self, repository_rootdir):
        self.repository_rootdir = repository_rootdir
    #~ def set_repository_rootdir()

    def set_repo_executables_relpaths(self, repo_executables_relpaths):
        self.repo_executables_relpaths = repo_executables_relpaths
    #~ def set_repo_executables_relpaths()

    def set_source_files_to_objects(self, source_files_to_objects):
        self.source_files_to_objects = source_files_to_objects
    #~ def set_source_files_to_objects()

    def set_dev_tests_list(self, dev_tests_list):
        self.dev_tests_list = dev_tests_list
    #~ def set_dev_tests_list()

    # Following methods are called by the caller. 
    # The above are called by repo manager
    
    def set_pre_callback_args (self, pre_callback_args ):
        self.pre_callback_args = pre_callback_args 
    #~ def set_pre_callback_args()

    def set_post_callback_args (self, post_callback_args ):
        self.post_callback_args = post_callback_args 
    #~ def set_post_callback_args()

    @abc.abstractmethod
    def before_command(self):
        """ This method is executed BEFORE the execution of the
            corrresponding command.
            :return: (bool) True on success and False on failure
        """
        pass

    @abc.abstractmethod
    def after_command(self):
        """ This method is executed AFTER the execution of the
            corrresponding command. The execution of the command return 
            the boolean value that is then set in 'self.op_retval' 
            (this is set to None prior execution of the command).
            :return: (bool) True on success, False on failure.
        """
        pass
#~ class BaseCallbackObject

class DefaultCallbackObject(BaseCallbackObject):
    """ Use this class object if no call back is needed
    """
    def before_command(self):
        """ Return True for success
        """
        return common_mix.GlobalConstants.COMMAND_SUCCESS
    #~ def before_command()

    def after_command(self):
        """ Return True for success
        """
        return common_mix.GlobalConstants.COMMAND_SUCCESS
    #~ def after_command()
#~ class DefaultCallbackObject
