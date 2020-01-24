#
# [LICENCE]
#
""" From Json file criteria test execution optimizer class
"""

from __future__ import print_function
import os
import sys
import copy
import logging

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

from muteria.drivers.optimizers.criteriatestexecution.tools.fromdict \
                            import CriteriaTestExecutionOptimizer as DictOpt

from muteria.drivers.optimizers.testexecution.tools.default \
                                                import TestExecutionOptimizer

ERROR_HANDLER = common_mix.ErrorHandler

class CriteriaTestExecutionOptimizer(DictOpt):
    def __init__(self, config, explorer, criterion, jsonfile=None):
        ERROR_HANDLER.assert_true(jsonfile is not None, \
                                        "jsonfile cannot be None", __file__)
        jsonobj = common_fs.loadJSON(jsonfile)
        DictOpt.__init__(self, config, explorer, criterion, dictobj=jsonobj)
    #~ def __init__()
#~ class CriteriaTestExecutionOptimizer

