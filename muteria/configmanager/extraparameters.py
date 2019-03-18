"""
This module implements the extraparameters which can be specifically set 
by each plugin (testtool, mutationtool, codeconverter, coveragetool, 
executionoptimizers,...).

The user can import this module and set the corresponding values
XXX try to use meaningful name for parameter in this format.
XXX These parameters will be set by the config manager using the user 
    given parameters.
"""

import muteria.common.mix as common_mix

class ExtraParameters(dict):
    # CODE CONVERTER (muteria.repositoryandcode.code_transformations)
    ## muteria.repositoryandcode.code_transformations.llvm
    LLVM_TO_NATIVE_LINKING_FLAGS = None

    # ----- ADD New pluggin Extr Params Here ^ ------#
#~ class ExtraParameters
