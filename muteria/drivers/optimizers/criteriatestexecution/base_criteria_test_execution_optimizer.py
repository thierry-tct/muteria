#
# [LICENCE]
#
""" Base test criteria test execution optimizer class (For a single criterion)

    Each file that implement a optimizer must have the class 
    `CriteriaTestExecutionOptimizer` that implements the base class bellow
"""

from __future__ import print_function
import os
import sys
import logging
import abc

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class BaseCriteriaTestExecutionOptimizer(abc.ABC):
    '''
    '''

    def __init__(self, config, explorer, criterion, **kwargs):
        # Set Direct Arguments Variables
        self.config = config
        self.explorer = explorer
        self.criterion = criterion

        self.test_objective_ordered_list = None
        self.pointer = None
        self.test_objective_to_test_execution_optimizer = None
    #~ def __init__()

    def get_test_execution_optimizer(self, test_objective):
        """ Get an initialized test execution optimizer 
            (the user should not reset)
        """
        ERROR_HANDLER.assert_true(test_objective in \
                            self.test_objective_to_test_execution_optimizer, \
                                                    "Invalid test objective")
        return self.test_objective_to_test_execution_optimizer[test_objective]
    #~ def get_test_execution_optimizer()

    def has_next_test_objective (self):
        return self.pointer < len(self.test_objective_ordered_list)
    #~ def has_next_test_objective()

    def get_next_test_objective (self):
        ERROR_HANDLER.assert_true(\
                                self.test_objective_ordered_list is not None, \
                                'uninitialized test_objective_ordered_list')
        if self.has_next_test_objective():
            ret = self.test_objective_ordered_list[self.pointer]
            self.pointer += 1
        else:
            ret = None
        return ret
    #~ def get_next_test_objective()

    def select_test_objectives(self, test_objective_list, proportion_number, \
                                                        is_proportion=True):
        """ Apply Mutant Selection
        """
        ERROR_HANDLER.assert_true(\
                self.test_objective_ordered_list is not None, \
                                    'uninitialized test_objective_order_list')
        ERROR_HANDLER.assert_true(proportion_number > 0, \
                                        'proportion_number must be positive')
        if is_proportion:
            ERROR_HANDLER.assert_true(proportion_number <= 100, \
                                        'proportion must be <= 100')
            proportion_number = round(len(self.test_objective_ordered_list) * \
                                                    proportion_number / 100.0)
            proportion_number = max(1, int(proportion_number))
        return self.test_objective_ordered_list[:proportion_number]
    #~ def select_test_objectives()

    def feedback (self, test_objective, test_to_verdict, **kwargs):
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
    def reset (self, toolalias, test_objective_list, test_list, **kwargs):
        """ Reset the optimizer 
            (compute test objective ordering and their test orderings)
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def reset()
#~ class BaseCriteriaTestExecutionOptimizer