#
# [LICENCE]
#
""" Base and Default test execution optimizer classes

    Each file that implement a optimizer must have the class 
    `TestExecutionOptimizer` that implements the base class bellow
"""

from __future__ import print_function
import os
import sys
import logging
import abc

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class BaseTestExecutionOptimizer(abc.ABC):
    '''
    '''

    def __init__(self, config, explorer, **kwargs):
        # Set Direct Arguments Variables
        self.config = config
        self.explorer = explorer

        self.test_ordered_list = None
        self.pointer = 0

        # by default not locked (can reset)
        self.reset_disabled = False
    #~ def __init__()

    def has_next_test (self):
        return self.pointer < len(self.test_ordered_list)
    #~ def has_next_test()

    def get_next_test (self):
        ERROR_HANDLER.assert_true(self.test_ordered_list is not None, \
                                            'uninitialized test_order_list')
        if self.has_next_test():
            ret = self.test_ordered_list[self.pointer]
            self.pointer += 1
        else:
            ret = None
        return ret
    #~ def get_next_test()

    def select_tests(self, proportion_number, is_proportion=True):
        """ Apply test Selection
        """
        ERROR_HANDLER.assert_true(self.test_ordered_list is not None, \
                                            'uninitialized test_order_list')
        ERROR_HANDLER.assert_true(proportion_number > 0, \
                                        'proportion_number must be positive')
        if is_proportion:
            ERROR_HANDLER.assert_true(proportion_number <= 100, \
                                        'proportion must be <= 100')
            proportion_number = round(len(self.test_ordered_list) * \
                                                    proportion_number / 100.0)
            proportion_number = max(1, int(proportion_number))
        return self.test_ordered_list[:proportion_number]
    #~ def select_tests()

    def feedback (self, test_case, verdict, **kwargs):
        """ Possibly get feedback from past executions
            Override this if needed
        """
    #~ def feedback()

    #######################################################################
    ##################### Methods to implement ############################
    #######################################################################

    @classmethod
    @abc.abstractclassmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def installed()

    @abc.abstractmethod
    def reset (self, toolalias, test_list, disable_reset=False, **kwargs):
        """ Reset the optimizer
            :param disable_reset: disable reset after this call to reset
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def reset()
#~ class BaseTestExecutionOptimizer