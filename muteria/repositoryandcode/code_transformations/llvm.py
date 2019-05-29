
from __future__ import print_function

import sys
import os
import logging
import shutil

import muteria.common.mix as common_mix

import muteria.repositoryandcode.codes_convert_support as ccs

ERROR_HANDLER = common_mix.ErrorHandler

__all__ = ['FromLLVMBitcode']

class FromLLVMBitcode(ccs.BaseCodeFormatConverter):
    def __init__(self):
        self.src_formats = [
            ccs.CodeFormats.LLVM_BITCODE,
        ]
        self.dest_formats = [
            ccs.CodeFormats.LLVM_BITCODE,
            ccs.CodeFormats.OBJECT_FILE,
            ccs.CodeFormats.NATIVE_CODE,
        ]
    #~ def __init__()

    def convert_code(self, src_fmt, dest_fmt, file_src_dest_map, \
                                                        repository_manager):
        ERROR_HANDLER.error_exit("Must Implement", __file__)
    #~ def identity_function()

    def get_source_formats(self):
        return self.src_formats
    #~ def get_source_formats()

    def get_destination_formats_for(self, src_fmt):
        return self.dest_formats
    #~ def get_destination_formats()
#~ class FromLLVMBitcode()