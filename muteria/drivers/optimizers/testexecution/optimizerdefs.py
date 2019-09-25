
from __future__ import print_function

import muteria.common.mix as common_mix

import muteria.drivers.optimizers.criteriatestexecution as crit_opt

class TestOptimizers(common_mix.EnumAutoName):
    def get_optimizer(self):
        return self.get_field_value()
    #~ def get_optimizer():
#~ class TestOptimizers
