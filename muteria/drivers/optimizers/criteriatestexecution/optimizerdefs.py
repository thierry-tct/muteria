
from __future__ import print_function

import importlib

import muteria.common.mix as common_mix

from muteria.drivers.criteria import TestCriteria

import muteria.drivers.optimizers.criteriatestexecution.tools as crit_opt

class CriteriaOptimizers(common_mix.EnumAutoName):
    # Default (No Optimization)
    NO_OPTIMIZATION = importlib.import_module(".default", \
                                                package=crit_opt.__name__
                                            ).CriteriaTestExecutionOptimizer

    # Strong Mutation
    SM_OPTIMIZED_BY_WM = importlib.import_module(\
                                        ".strongmutation_by_weakmutation", \
                                        package=crit_opt.__name__
                                    ).CriteriaTestExecutionOptimizer
    SM_OPTIMIZED_BY_MCOV = importlib.import_module(\
                                        ".strongmutation_by_mutantcoverage", \
                                        package=crit_opt.__name__
                                    ).CriteriaTestExecutionOptimizer

    def get_optimizer(self):
        return self.get_field_value()
    #~ def get_optimizer():
#~ class CriteriaOptimizers

# TODO: Make a function to check that the optimizer specified is for the right criterion
def check_is_right_optimizer(criterion, optimizer):
    """ Check that the optimizer is fit for the criterion
        :return: True if fit, False otherwise
    """
    dat = {
        TestCriteria.STRONG_MUTATION: {
            CriteriaOptimizers.SM_OPTIMIZED_BY_MCOV,
            CriteriaOptimizers.SM_OPTIMIZED_BY_WM,
        }
    }

    # Check
    if criterion in dat:
        if optimizer in dat[criterion]:
            return True
    return False
#~ def check_right_optimizer()