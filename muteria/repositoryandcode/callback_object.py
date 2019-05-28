
from __future__ import print_function

import abc

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

    def set_op_retval(self, op_retval):
        self.op_retval = op_retval
    #~ def set_op_retval()
    
    def set_pre_callback_args (self, pre_callback_args ):
        self.pre_callback_args = pre_callback_args 
    #~ def set_pre_callback_args()

    def set_post_callback_args (self, post_callback_args ):
        self.post_callback_args = post_callback_args 
    #~ def set_post_callback_args()

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

    @abc.abstractmethod
    def before_command(self):
        """ This method is executed BEFORE the execution of the the 
            corrresponding command.
            :return: (bool) True on success and False on failure
        """
        pass

    @abc.abstractmethod
    def after_command(self):
        """ This method is executed AFTER the execution of the the 
            corrresponding command. The execution of the command return 
            the boolean value that is then set in 'self.op_retval' 
            (this is set to None prior execution of the command).
            :return: (bool) True on success, False on failure.
        """
        pass
#~ class BaseCallbackObject

class DefaultCallbackObject(BaseCallbackObject):
    """ Use this class object it no call back is needed
    """
    def before_command(self):
        """ Return True for success
        """
        return True
    #~ def before_command()

    def after_command(self):
        """ Returns the same code as the executed command
        """
        return self.op_retval
    #~ def after_command()
#~ class DefaultCallbackObject