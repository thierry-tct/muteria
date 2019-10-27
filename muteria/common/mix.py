""" This Module implement some utility mathods used throughout the project.
        - The function `confirm_execution` is usefule to request user
            confirmation before proceeding the execution of a task that 
            is considered important to verify user certainty in proceeding.
            An example is the deletion of the data directory...
        - The class `ErrorHandler` define function that are called to 
            terminate the execution gracefully and informativelly 
            upon error. 
"""

from __future__ import print_function

import sys
import shutil
import logging
import inspect
import traceback

import enum

def confirm_execution(question):
    """
    Ask user to enter Y or N (case-insensitive).

    :return: True if the answer is Y.
    :rtype: bool
    """
    reading_func = input
    if sys.version_info.major < 3:
        reading_func = eval('raw_input')
    answer = ""
    while answer not in ["y", "n"]:
        answer = reading_func("%s %s" % (question, "[Y/N] ")).lower()
    return answer == "y"
#~ def confirm_execution()

class ErrorHandler(object):
    repos_dir_manager = None
    # Make sure that there is no infinite recursive call to error_exit
    # if the function `RepositoryManager.revert_repository` make a call
    # to `error_exit`
    error_exit_revert_repo_called = False
    
    def __init__(self):
        pass

    @classmethod
    def set_corresponding_repos_manager(cls, repos_dir_manager):
        cls.assert_true (cls.repos_dir_manager is None, \
                            err_string="the repo dir manager is already set", \
                            call_location=__file__)
        cls.repos_dir_manager = repos_dir_manager
    #~ def set_corresponding_repos_manager()

    @classmethod
    def error_exit(cls, err_string=None, call_location=None, error_code=1, \
                                        ask_revert=True, from_assert=False):
        #traceback.print_stack()
        logging.error('\n'+''.join(traceback.format_stack()))
        if call_location is not None:
            logging.error("# Error happened in location {}".format(\
                                                            call_location))
        if from_assert:
            last_function = inspect.stack()[2][3]
        else:
            last_function = inspect.stack()[1][3]
        logging.error("# Error happened in function %s" % last_function)
                                                        
        if err_string:
            logging.error('')
            logging.error(" (msg) "+err_string)
            logging.error('')
        if ask_revert and cls.repos_dir_manager is not None:
            if cls.error_exit_revert_repo_called:
                logging.error("@ post error: Failed to revert repository."
                                "DO IT MANUALLY!!")
            elif confirm_execution("Do you want to revert repository files?"):
                logging.info("@ post error: Reverting repository files")
                cls.error_exit_revert_repo_called = True
                cls.repos_dir_manager.revert_repository(as_initial=False)
        else:
            logging.info("@ post error: Manually revert the repository files")
        logging.info("# Exiting with code %d" % error_code)
        sys.exit(error_code)
    #~ def error_exit()

    @classmethod
    def assert_true(cls, condition, err_string=None, \
                                call_location=None, ask_revert=True):
        '''
        Call this function with the parameter *__file__*
        as location_called_from
        '''
        if not condition:
            cls.error_exit(err_string=err_string, \
                            call_location=call_location, \
                            ask_revert=ask_revert, from_assert=True)
    #~ def error_exit_file()
#~ class ErrorHandler

class GlobalConstants(object):
    UNCERTAIN_TEST_VERDICT = None

    PASS_TEST_VERDICT = 0
    
    FAIL_TEST_VERDICT = 1

    TEST_EXECUTION_ERROR = -1
    
    ELEMENT_UNCERTAIN_VERDICT = None

    ELEMENT_COVERED_VERDICT = 1
    
    ELEMENT_NOTCOVERED_VERDICT = 0

    COMMAND_UNCERTAIN = None

    COMMAND_SUCCESS = 0

    COMMAND_FAILURE = 1
#~ class GlobalConstants

@enum.unique
class EnumAutoName(enum.Enum):
    
    """ This is a base class that can be used to define enums, 
        Extend this class to generate an enum that will have the methods
        defined here.
    """
        
        # This function do not have 'self'
    #def _generate_next_value_(name, start, count, last_values):
        #return name

    def get_str(self):
        """ get the string representation of the enum field.
            Example:
            >>> class MyEnum(EnumAutoName):
            ...     FIELD1 = "abc"
            ...     FIELD2 = 3
            ...
            >>> my = MyEnum
            >>> my.FIELD1.get_str()
            'FIELD1'
        """
        return self.name
    #~ def get_str():

    def get_field_value(self):
        """ get the value of the enum field.
            Example:
            >>> class MyEnum(EnumAutoName):
            ...     FIELD1 = "abc"
            ...     FIELD2 = 3
            ...
            >>> my = MyEnum
            >>> my.FIELD1.get_field_value()
            'abc'
        """
        return self.value
    #~ def get_field_value():

    @classmethod
    def has_element_named(cls, e_name):
        """ Check that the string e_name represent the name of a field
            of the enum.
            Example:
            >>> class MyEnum(EnumAutoName):
            ...     FIELD1 = "abc"
            ...     FIELD2 = 3
            ...
            >>> MyEnum.has_element_named("FIELD1")
            True
            >>> MyEnum.has_element_named("xyz")
            False
        """
        return e_name in cls.__members__
    #~ def has_element_named()
    
    @classmethod
    def is_valid(cls, elem):
        """ Check that the object elem is a field of the enum
            Example:
            >>> class MyEnum(EnumAutoName):
            ...     FIELD1 = "abc"
            ...     FIELD2 = 3
            ...
            >>> MyEnum.is_valid(MyEnum.FIELD1)
            True
            >>> MyEnum.is_valid("FIELD1")
            False
        """
        return elem in cls
    #~ def is_valid()
#~ class EnumAutoName
