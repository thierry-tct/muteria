
from __future__ import print_function

import sys
import os
import logging
import shutil

import muteria.common.mix as common_mix

import muteria.repositoryandcode.code_builds_factory as cbf

ERROR_HANDLER = common_mix.ErrorHandler

__all__ = ['FromC', 'FromCpp']

class FromC(cbf.BaseCodeFormatConverter):
    def __init__(self):
        self.src_formats = [
            cbf.CodeFormats.C_SOURCE,
            cbf.CodeFormats.C_PREPROCESSED_SOURCE
        ]
        self.dest_formats = [
            cbf.CodeFormats.C_PREPROCESSED_SOURCE,
            cbf.CodeFormats.LLVM_BITCODE,
            cbf.CodeFormats.OBJECT_FILE,
            cbf.CodeFormats.NATIVE_CODE,
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
#~ class FromC

class FromCpp(cbf.BaseCodeFormatConverter):
    def __init__(self):
        self.src_formats = [
            cbf.CodeFormats.CPP_SOURCE,
            cbf.CodeFormats.CPP_PREPROCESSED_SOURCE
        ]
        self.dest_formats = [
            cbf.CodeFormats.CPP_PREPROCESSED_SOURCE,
            cbf.CodeFormats.LLVM_BITCODE,
            cbf.CodeFormats.OBJECT_FILE,
            cbf.CodeFormats.NATIVE_CODE,
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
#~ class FromCpp