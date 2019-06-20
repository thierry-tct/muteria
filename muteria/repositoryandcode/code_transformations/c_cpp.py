
from __future__ import print_function

import sys
import os
import logging
import shutil

import muteria.common.mix as common_mix

import muteria.repositoryandcode.codes_convert_support as ccs
from muteria.repositoryandcode.callback_object import DefaultCallbackObject

ERROR_HANDLER = common_mix.ErrorHandler

__all__ = ['FromC', 'FromCpp']

class FromC(ccs.BaseCodeFormatConverter):
    def __init__(self):
        self.src_formats = [
            ccs.CodeFormats.C_SOURCE,
            ccs.CodeFormats.C_PREPROCESSED_SOURCE
        ]
        self.dest_formats = [
            ccs.CodeFormats.C_PREPROCESSED_SOURCE,
            ccs.CodeFormats.LLVM_BITCODE,
            ccs.CodeFormats.OBJECT_FILE,
            ccs.CodeFormats.NATIVE_CODE,
        ]
    #~ def __init__()

    def convert_code(self, src_fmt, dest_fmt, file_src_dest_map, \
                                                repository_manager, **kwargs):
        # TODO: add can_fail parameter, in kwarg, for case like mutant
        # compilatioon that can fail but should not terminate execution
        # but return a specific value
        ERROR_HANDLER.assert_true(src_fmt in self.src_formats, \
                                    "Unsupported src format", __file__)

        # post build callbacks
        class CopyCallbackObject(DefaultCallbackObject):
            def after_command(self):
                if self.op_retval == \
                                    common_mix.GlobalConstants.COMMAND_FAILURE:
                    return common_mix.GlobalConstants.COMMAND_FAILURE
                for sf, df in list(file_src_dest_map.items()):
                    abs_sf = repository_manager.repo_abs_path(sf)
                    if not os.path.isfile(abs_sf):
                        ERROR_HANDLER.error_exit(\
                                "an expected file missing after build: "+\
                                                            abs_sf, __file__)
                    if df is not None:
                        shutil.copy2(abs_sf, df)
                return None
            #~ def after_command()
        #~ class CopyCallbackObject

        # Should not have callback_object and file_src_dest_map at the
        # same time
        callbak_obj_key = 'callback_object'
        if callbak_obj_key in kwargs:
            ERROR_HANDLER.assert_true(file_src_dest_map is None,\
                            "file_src_dest_map must be None "+ \
                            "if callback_object is passed", __file__)
        elif file_src_dest_map is not None and len(file_src_dest_map) > 0:
            kwargs[callbak_obj_key] = CopyCallbackObject()
        else:
            kwargs[callbak_obj_key] = None

        # Actual Processing
        if (dest_fmt == ccs.CodeFormats.C_PREPROCESSED_SOURCE):
            if (src_fmt == ccs.CodeFormats.C_SOURCE):
                ERROR_HANDLER.error_exit("Must Implement1", __file__)
            else:
                for src, dest in list(file_src_dest_map.items()):
                    shutil.copy2(src, dest)
        if (dest_fmt == ccs.CodeFormats.LLVM_BITCODE):
            ERROR_HANDLER.error_exit("Must Implement2", __file__)
        if (dest_fmt == ccs.CodeFormats.OBJECT_FILE):
            ERROR_HANDLER.error_exit("Must Implement3", __file__)
        if (dest_fmt == ccs.CodeFormats.NATIVE_CODE):
            pre_ret, ret, post_ret = repository_manager.build_code(**kwargs)
        return pre_ret, ret, post_ret
    #~ def convert_code()

    def get_source_formats(self):
        return self.src_formats
    #~ def get_source_formats()

    def get_destination_formats_for(self, src_fmt):
        return self.dest_formats
    #~ def get_destination_formats()
#~ class FromC

class FromCpp(ccs.BaseCodeFormatConverter):
    def __init__(self):
        self.src_formats = [
            ccs.CodeFormats.CPP_SOURCE,
            ccs.CodeFormats.CPP_PREPROCESSED_SOURCE
        ]
        self.dest_formats = [
            ccs.CodeFormats.CPP_PREPROCESSED_SOURCE,
            ccs.CodeFormats.LLVM_BITCODE,
            ccs.CodeFormats.OBJECT_FILE,
            ccs.CodeFormats.NATIVE_CODE,
        ]
    #~ def __init__()

    def convert_code(self, src_fmt, dest_fmt, file_src_dest_map, \
                                                repository_manager, **kwargs):
        ERROR_HANDLER.error_exit("Must Implement", __file__)
    #~ def identity_function()

    def get_source_formats(self):
        return self.src_formats
    #~ def get_source_formats()

    def get_destination_formats_for(self, src_fmt):
        return self.dest_formats
    #~ def get_destination_formats()
#~ class FromCpp