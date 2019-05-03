
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
                                                repository_manager, **kwargs):
        ERROR_HANDLER.assert_true(src_fmt in self.src_formats, \
                                    "Unsupported src format", __file__)

        # post build callbacks
        def _copy_files(build_ret):
            if not build_ret:
                return repository_manager.ERROR
            for sf, df in list(file_src_dest_map.items()):
                abs_sf = repository_manager.repo_abs_path(sf)
                if not os.path.isfile(abs_sf):
                    ERROR_HANDLER.error_exit(\
                            "an expected file missing after build: "+abs_sf,\
                                                                    __file__)
                shutil.copy2(abs_sf, df)
            if 'post_process_callback' in kwargs:
                ERROR_HANDLER.error_exit(
                            "Not yet handle passing callback to merge here",\
                                                                    __file__)
            return None
        #~ def _copy_files()

        if (dest_fmt == cbf.CodeFormats.C_PREPROCESSED_SOURCE):
            if (src_fmt == cbf.CodeFormats.C_SOURCE):
                ERROR_HANDLER.error_exit("Must Implement1", __file__)
            else:
                for src, dest in list(file_src_dest_map.items()):
                    shutil.copy2(src, dest)
        if (dest_fmt == cbf.CodeFormats.LLVM_BITCODE):
            ERROR_HANDLER.error_exit("Must Implement2", __file__)
        if (dest_fmt == cbf.CodeFormats.OBJECT_FILE):
            ERROR_HANDLER.error_exit("Must Implement3", __file__)
        if (dest_fmt == cbf.CodeFormats.NATIVE_CODE):
            pre_ret, post_ret = repository_manager.build_code(\
                                            post_process_callback=_copy_files,\
                                                                    **kwargs)
            ERROR_HANDLER.assert_true(pre_ret, \
                                        "BUG, no pre_ret but False", __file__)
            ERROR_HANDLER.assert_true(post_ret is None, \
                                                "post_ret failure", __file__)
        return True
    #~ def convert_code()

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