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
import muteria.common.matrices as common_matrices

import muteria.controller.explorer as explorer
from muteria.drivers import DriversUtils
from muteria.drivers.criteria import TestCriteria

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

        # get the test list per test objectives, based on the matrix
        opt_by_criterion = self._get_optimizing_criterion()
        matrix_file = self.explorer.get_existing_file_pathname(\
                                explorer.TMP_CRITERIA_MATRIX[opt_by_criterion])
        test_list_per_test_objective = \
                            self._get_test_objective_tests_from_matrix(\
                                                    matrix_file=matrix_file)

        # Update test list
        for to, teo in self.test_objective_to_test_execution_optimizer.items():
            alias_to = DriversUtils.make_meta_element(to, toolalias)
            ERROR_HANDLER.assert_true(\
                                    alias_to in test_list_per_test_objective, \
                                    "Bug: test objective missing("+str(to)+')')
            teo.reset(None, test_list_per_test_objective[alias_to], \
                                                            disable_reset=True)
    #~ def reset()

    ##### Private methods #####
    
    def _get_optimizing_criterion(self):
        return TestCriteria.WEAK_MUTATION
    #~ def _get_optimizing_criterion()

    def _get_test_objective_tests_from_matrix (self, matrix_file):
        matrix = common_matrices.ExecutionMatrix(filename=matrix_file)
        res = matrix.query_active_columns_of_rows()
        return res
    #~ def _get_test_objective_tests_from_matrix ()
#~ class CriteriaTestExecutionOptimizer

