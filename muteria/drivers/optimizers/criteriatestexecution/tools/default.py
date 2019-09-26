#
# [LICENCE]
#
""" Default criteria test execution optimizer class
"""

from __future__ import print_function
import os
import sys
import copy
import logging

import muteria.common.mix as common_mix

from muteria.drivers.optimizers.criteriatestexecution.\
                                base_criteria_test_execution_optimizer \
                                    import BaseCriteriaTestExecutionOptimizer

from muteria.drivers.optimizers.testexecution.tools.default \
                                                import TestExecutionOptimizer

ERROR_HANDLER = common_mix.ErrorHandler

class CriteriaTestExecutionOptimizer(BaseCriteriaTestExecutionOptimizer):

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

    def reset (self, toolalias, test_objective_list, test_list, **kwargs):
        """ Reset the optimizer
        """
        self.test_objective_ordered_list = copy.deepcopy(test_objective_list)
        self.pointer = 0
        self.test_objective_to_test_execution_optimizer = {
            to: TestExecutionOptimizer(self.config, self.explorer, \
                                                        disable_reset=True) \
            for to in self.test_objective_ordered_list
        }
        for _, teo in self.test_objective_to_test_execution_optimizer.items():
            teo.reset(test_list, disable_reset=True)
    #~ def reset()
#~ class CriteriaTestExecutionOptimizer

