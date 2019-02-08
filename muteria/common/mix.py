""" This Module implement some utility mathods used throughout the project.
        - The function `confirm_execution` is usefule to request user
            confirmation before proceeding the execution of a task that 
            is considered important to verify user certainty in proceeding.
            An example is the deletion of the data directory...
        - The class `ErrorHandler` define function that are called to 
            terminate the execution gracefully and informativelly 
            upon error. 
            TODO: Implement revert in the ErrorHandler.error_exit function
"""

from __future__ import print_function

import sys
import shutil
import logging
import inspect

#import muteria.common.reposutils as common_reposutils


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
    def __init__(self):
        pass

    @classmethod
    def error_exit(cls, error_code=1, err_string=None, ask_revert=True):
        logging.error("#Error happened in function %s" % inspect.stack()[1][3])
        if err_string:
            logging.error(err_string)
        if ask_revert:
            if confirm_execution("Do you want to revert repository files?"):
                logging.info("@post error: Reverting repository files")
                # TODO implement revert
        else:
            logging.info("@post error: Manually revert the repository files")
        print("# Exiting with code %d" % error_code)
        exit(error_code)

    @classmethod
    def error_exit_file(cls, file_called_from, error_code=1, \
                                    err_string=None, ask_revert=True):
        '''
        Call this function with the parameter *__file__*
        '''
        logging.error("# Error happened in file %s" % file_called_from)
        cls.error_exit(error_code=error_code, err_string=err_string, \
                                                    ask_revert=ask_revert)
#~ class ErrorHandler
