
from __future__ import print_function

import sys
import os
import logging
import shutil

import muteria.common.mix as common_mix

import muteria.repositoryandcode.code_builds_factory as cbf

ERROR_HANDLER = common_mix.ErrorHandler

__all__ = ['FromLLVMBitcode']

class FromLLVMBitcode(cbf.BaseCodeFormatConverter):
    def __init__(self):
        pass
    #~ def __init__()

    def convert_code(self, src_fmt, dest_fmt, file_src_dest_map, \
                                                        repository_manager):
        ERROR_HANDLER.error_exit("Must Implement", __file__)
    #~ def identity_function()

    def get_source_formats(self):
        ERROR_HANDLER.error_exit("Must Implement", __file__)
    #~ def get_source_formats()

    def get_destination_formats_for(self, src_fmt):
        ERROR_HANDLER.error_exit("Must Implement", __file__)
    #~ def get_destination_formats()
#~ class FromLLVMBitcode()