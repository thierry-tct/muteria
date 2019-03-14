"""
"""

from __future__ import print_function

import sys
import os
import logging
import shutil
import abc

import muteria.common.mix as common_mix

import muteria.repositoryandcode.code_transformations as ct_modules

ERROR_HANDLER = common_mix.ErrorHandler

class CodeFormats(common_mix.EnumAutoName):
    NATIVE_CODE = "NATIVE_CODE"
    OBJECT_FILE = "OBJECT_FILE"
    ASSEMBLY_CODE = "ASSEMBLY_CODE"

    LLVM_BITCODE = "LLVM_BITCODE"

    C_SOURCE = "C_SOURCE"
    C_PREPROCESSED_SOURCE = "C_PREPROCESSED_SOURCE"
    CPP_SOURCE = "CPP_SOURCE"
    CPP_PREPROCESSED_SOURCE = "CPP_PREPROCESSED_SOURCE"

    JAVA_SOURCE = "JAVA_SOURCE"
    JAVA_BITCODE = "JAVA_BITCODE"

    PYTHON_SOURCE = "PYTHON_SOURCE"
    JAVASCRIPT_SOURCE = "JAVASCRIPT_SOURCE"

#~ class CodeFormats()

class BaseCodeFormatConverter(abc.ABC):
    @abc.abstractmethod
    def convert_code(self, file_src_dest_map, src_fmt, dest_fmt, **kwargs):
        pass

    @abc.absractmethod
    def get_source_formats(self):
        pass

    @abc.absractmethod
    def get_destination_formats(self, src_fmt):
        pass
#~ class BaseCodeFormatConverter

class IdentityCodeConverter(BaseCodeFormatConverter):
    def convert_code(self, file_src_dest_map, src_fmt, dest_fmt, **kwargs):
        # make sure that different sources have different destinations
        ERROR_HANDLER.assert_true(len(file_src_dest_map) == \
                    len({file_src_dest_map[fn] for fn in file_src_dest_map}), \
                        "Must specify one destination for each file", __file__)
        # copy the sources into the destinations
        file_src_dest_map = dict()
        for src, dest in list(file_src_dest_map.items()):
            if os.path.abspath(src) != os.path.abspath(dest):
                shutil.copy2(src, dest)
    #~ def identity_function()

    def get_source_formats(self):
        ERROR_HANDLER.error_exit(\
                    "get_source_formats must not be called here", __file__)
    def get_destination_formats(self, src_fmt):
        ERROR_HANDLER.error_exit(\
                "get_destination_formats must not be called here", __file__)
#~ class IdentityCodeConverter

formatfrom_formatto_function_tuples = [
    # From C and CPP source
    (CodeFormats.C_SOURCE, ct_modules.c_cpp.FromC()),
    (CodeFormats.C_PREPROCESSED_SOURCE, ct_modules.c_cpp.FromC()),
    (CodeFormats.CPP_SOURCE, ct_modules.c_cpp.FromCpp()),
    (CodeFormats.CPP_PREPROCESSED_SOURCE, ct_modules.c_cpp.FromCpp()),

    # From LLVM bitcode
    (CodeFormats.LLVM_BITCODE, ct_modules.llvm.FromLLVMBitcode()),

    # From Javascript source
    (CodeFormats.JAVASCRIPT_SOURCE, IdentityCodeConverter()),
]

class CodeBuildsFactory(object):
    def __init__(self):
        self.src_dest_fmt_to_handling_obj = {}

        # Initialize 
        for src_fmt, obj_cls in formatfrom_formatto_function_tuples:
            if isinstance(obj_cls, IdentityCodeConverter):
                self._fmt_from_to_registration(src_fmt, src_fmt, obj_cls)
            else:
                ERROR_HANDLER.assert_true(\
                                src_fmt in obj_cls.get_source_formats, \
                                "{} {} {} {}".format( \
                            "Error in 'formatfrom_formatto_function_tuples'",
                            "src_fmt", src_fmt, "not in corresponding obj..."),
                                                                    __file__)
                for dest_fmt in obj_cls.get_destination_formats_for(src_fmt):
                    self._fmt_from_to_registration(src_fmt, dest_fmt, obj_cls)

    #~ def __init__()

    def _fmt_from_to_registration(self, src_fmt, dest_fmt, handling_obj):
        if src_fmt not in self.src_dest_fmt_to_handling_obj:
            self.src_dest_fmt_to_handling_obj[src_fmt] = {}
        ERROR_HANDLER.assert_true( \
                dest_fmt not in self.src_dest_fmt_to_handling_obj[src_fmt],
                "dest_fmt {} added twice for same src_fmt {}".format( \
                                                src_fmt, dest_fmt), __file__)
        self.src_dest_fmt_to_handling_obj[src_fmt][dest_fmt] = handling_obj
    #~ def _fmt_from_to_registration()

    def transform_src_into_dest (self, src_fmt, dest_fmt, \
                                            src_dest_files_paths_map, **kwars):
        # TODO
    #~ def transform_src_into_dest ()
    
    def override_registration (self, src_fmt, dest_fmt, handling_obj):
        # TODO: set another obj to handle src dest pair
    #~ def override_registration ():
#~ class CodeBuildsFactory()