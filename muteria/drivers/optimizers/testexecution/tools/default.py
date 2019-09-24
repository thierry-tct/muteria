#
# [LICENCE]
#
""" Default test execution optimizer classes
"""

from __future__ import print_function
import os
import sys
import copy
import logging

import muteria.common.mix as common_mix

from muteria.drivers.optimizers.testexecution.base_test_execution_optimizer \
                                            import BaseTestExecutionOptimizer

ERROR_HANDLER = common_mix.ErrorHandler

class TestExecutionOptimizer(BaseTestExecutionOptimizer):

    def __init__(self, config, explorer, language, disable_reset=False, \
                                                                    **kwargs):
        # Set Direct Arguments Variables
        self.config = config
        self.explorer = explorer
        self.disable_reset = disable_reset

        self.test_ordered_list = {}
        self.pointer = 0
    #~ def __init__()

    #######################################################################
    ##################### Methods implemented ############################
    #######################################################################

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
    #~ def installed()

    def reset (self, test_list, **kwargs):
        """ Reset the optimizer
        """
        ERROR_HANDLER.assert_true(not self.disable_reset, "reset is disabled")
        self.test_ordered_list = copy.deepcopy(test_list)
    #~ def reset()

    def select_test(self, proportion_number, is_proportion=True):
        """ Apply test Selection
        """
        ERROR_HANDLER.assert_true(proportion_number > 0, \
                                        'proportion_number must be positive')
        if is_proportion:
            ERROR_HANDLER.assert_true(proportion_number <= 100, \
                                        'proportion must be <= 100')
            proportion_number = int(len(self.test_ordered_list) * \
                                                    proportion_number / 100.0)
            proportion_number = max(1, proportion_number)
        return self.test_ordered_list[:proportion_number]
    #~ def select_test()

    def get_next_test (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def get_next_test()

    def has_next_test (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def has_next_test()
#~ class TestExecutionOptimizer
