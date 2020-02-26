#
# [LICENCE]
#
""" From dict criteria test execution optimizer class
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

from muteria.drivers import DriversUtils

ERROR_HANDLER = common_mix.ErrorHandler

class CriteriaTestExecutionOptimizer(BaseCriteriaTestExecutionOptimizer):

    def __init__(self, config, explorer, criterion, dictobj=None):
        ERROR_HANDLER.assert_true(dictobj is not None, \
                                        "dictobj cannot be None", __file__)
        BaseCriteriaTestExecutionOptimizer.__init__(self, config, explorer, \
                                                                    criterion)
        # test objectives and tests are meta here
        self.dictobj = dictobj
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
        return True
    #~ def installed()

    def reset (self, toolalias, test_objective_list, test_list, **kwargs):
        """ Reset the optimizer
        """
        # Make sure that all objectives in test_objective_list are in dictobj
        # and get test_of_testobjective
        test_of_to = {}
        for to in test_objective_list:
            meta_to = DriversUtils.make_meta_element(to, toolalias)
            ERROR_HANDLER.assert_true(meta_to in self.dictobj, \
                                "meta test objective {} not in self.dictobj"\
                                                    .format(meta_to), __file__)
            test_of_to[to] = self.dictobj[meta_to]

            # If None as testlist, use all tests
            if test_of_to[to] is None:
                test_of_to[to] = test_list
            else:
                test_of_to[to] = list(set(test_list) & set(test_of_to[to]))

        self.test_objective_ordered_list = copy.deepcopy(test_objective_list)
        self.pointer = 0
        self.test_objective_to_test_execution_optimizer = {
            to: TestExecutionOptimizer(self.config, self.explorer) \
            for to in self.test_objective_ordered_list
        }
        for to, teo in self.test_objective_to_test_execution_optimizer.items():
            teo.reset(None, test_of_to[to], disable_reset=True)
    #~ def reset()
#~ class CriteriaTestExecutionOptimizer

