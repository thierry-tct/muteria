
from __future__ import print_function

import importlib

import muteria.common.mix as common_mix

import muteria.drivers.optimizers.testexecution.tools as test_opt

class TestOptimizers(common_mix.EnumAutoName):
    # Default (No Optimization)
    NO_OPTIMIZATION = importlib.import_module(".default", \
                                                package=test_opt.__name__
                                            ).TestExecutionOptimizer

    def get_optimizer(self):
        return self.get_field_value()
    #~ def get_optimizer():
#~ class TestOptimizers
