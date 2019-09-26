#
# [LICENCE]
#
""" Default test execution optimizer class
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

    def reset (self, toolalias, test_list, disable_reset=False, **kwargs):
        """ Reset the optimizer
        """
        ERROR_HANDLER.assert_true(not self.reset_disabled, "reset is disabled")
        self.test_ordered_list = copy.deepcopy(test_list)
        self.pointer = 0
    #~ def reset()
#~ class TestExecutionOptimizer
