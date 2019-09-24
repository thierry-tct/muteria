#
# [LICENCE]
#
""" Base test criteria test execution optimizer classes

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

    def __init__(self, config, explorer, language, **kwargs):
        # Set Direct Arguments Variables
        self.config = config
        self.explorer = explorer

        self.test_objective_to_test_execution_optimizer = {}
    #~ def __init__()

    def feedback (self, test_objective, verdict_list, **kwargs):
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
    def reset (self, test_objective_list, test_list, **kwargs):
        """ Reset the optimizer
        """
    #~ def reset()

    @abc.abstractmethod
    def get_test_execution_optimizer(self, test_objective):
        """ Get an initialized test execution optimizer 
            (the user should not reset)
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def get_test_execution_optimizer()


    @abc.abstractmethod
    def select_test_objectives(self, test_objective_list, proportion_number, \
                                                        is_proportion=True):
        """ Apply Mutant Selection
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def select_test_objectives()

    @abc.abstractmethod
    def get_next_test_objective (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def get_next_test_objective()

    @abc.abstractmethod
    def has_next_test_objective (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def has_next_test_objective()
#~ class BaseCriteriaTestExecutionOptimizer