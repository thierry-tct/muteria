
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import re

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.drivers.testgeneration.base_testcasetool import BaseTestcaseTool
from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject
from muteria.drivers import DriversUtils

from muteria.drivers.testgeneration.tools_by_languages.c.klee.klee \
                                                    import TestcasesToolKlee

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesToolShadowSE(TestcasesToolKlee):
    """ Make sure to set the path to binarydir in user customs to use this
        The path to binary should be set to the path to the shadow 
        directory. in Shadow VM, it should be '/home/shadowvm/shadow'
    """

#~ class TestcasesToolShadowSE