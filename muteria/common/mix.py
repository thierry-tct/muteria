#
#

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
        reading_func = raw_input
    answer = ""
    while answer not in ["y", "n"]:
        answer = reading_func("%s %s" % (question, "[Y/N] ")).lower()
    return answer == "y"
#~ def confirm_execution()

class ErrorHandler(object):
    def __init__(self):
        pass

    def error_exit(self, error_code=1, err_string=None, ask_revert=True):
        logging.error("#Error happened in function %s" % inspect.stack()[1][3])
        if err_string:
            logging.error(err_string)
        if ask_revert and \
                confirm_execution("Do you want to revert repository files?"):
            logging.info("Reverting repository files")
            # TODO implement revert
        print("# Exiting with code %d" % error_code)
        exit(error_code)

    def error_exit_file(self, file_called_from, error_code=1, \
                                    err_string=None, ask_revert=True):
        '''
        Call this function with the parameter __file__
        '''
        logging.error("# Error happened in file %s" % file_called_from)
        self.error_exit(error_code=error_code, err_string=err_string, \
                                                    ask_revert=ask_revert)
#~ class ErrorHandler
