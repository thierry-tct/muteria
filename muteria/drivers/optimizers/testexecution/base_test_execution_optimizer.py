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

    def __init__(self, config, explorer, language, disable_reset=False, \
                                                                    **kwargs):
        # Set Direct Arguments Variables
        self.config = config
        self.explorer = explorer

        self.test_ordered_list = {}
        self.pointer = 0
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
    def reset (self, test_list, **kwargs):
        """ Reset the optimizer
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def reset()

    @abc.abstractmethod
    def select_test(self, test_list, proportion_number, is_proportion=True):
        """ Apply test Selection
        """
        print ("!!! Must be implemented in child class !!!")
    #~ def select_test()

    @abc.abstractmethod
    def get_next_test (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def get_next_test()

    @abc.abstractmethod
    def has_next_test (self):
        print ("!!! Must be implemented in child class !!!")
    #~ def has_next_test()
#~ class BaseTestExecutionOptimizer