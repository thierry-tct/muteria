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
from muteria.drivers.criteria import TestCriteria

import muteria.drivers.optimizers.criteriatestexecution.tools.\
                                        strongmutation_by_weakmutation as sm_wm

from muteria.drivers.optimizers.testexecution.tools.default \
                                                import TestExecutionOptimizer

ERROR_HANDLER = common_mix.ErrorHandler

class CriteriaTestExecutionOptimizer(sm_wm.CriteriaTestExecutionOptimizer):

    #######################################################################
    ##################### Methods implemented ############################
    #######################################################################

    ##### Private methods #####
    
    def _get_optimizing_criterion(self):
        return TestCriteria.MUTANT_COVERAGE
    #~ def _get_optimizing_criterion()
#~ class CriteriaTestExecutionOptimizer

