"""
"""

from __future__ import print_function

import sys
import os
import logging

import muteria.common.mix as common_mix

import muteria.repositoryandcode.code_transformations as ct_modules
import muteria.repositoryandcode.codes_convert_support as ccs

ERROR_HANDLER = common_mix.ErrorHandler

formatfrom_function_tuples = [
    # From C and CPP source
    (ccs.CodeFormats.C_SOURCE, ct_modules.c_cpp.FromC()),
    (ccs.CodeFormats.C_PREPROCESSED_SOURCE, ct_modules.c_cpp.FromC()),
    (ccs.CodeFormats.CPP_SOURCE, ct_modules.c_cpp.FromCpp()),
    (ccs.CodeFormats.CPP_PREPROCESSED_SOURCE, ct_modules.c_cpp.FromCpp()),

    # From LLVM bitcode
    (ccs.CodeFormats.LLVM_BITCODE, ct_modules.llvm.FromLLVMBitcode()),

    # From Javascript source
    (ccs.CodeFormats.JAVASCRIPT_SOURCE, ccs.IdentityCodeConverter()),
]

class CodeBuildsFactory(object):
    def __init__(self, repository_manager):
        self.repository_manager = repository_manager
        self.src_dest_fmt_to_handling_obj = {}

        # Initialize 
        for src_fmt, obj_cls in formatfrom_function_tuples:
            if isinstance(obj_cls, ccs.IdentityCodeConverter):
                self._fmt_from_to_registration(src_fmt, src_fmt, obj_cls)
            else:
                ERROR_HANDLER.assert_true(\
                                src_fmt in obj_cls.get_source_formats, \
                                "{} {} {} {}".format( \
                            "Error in 'formatfrom_function_tuples'",
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
                                        src_dest_files_paths_map, **kwargs):
        # Checks
        ERROR_HANDLER.assert_true( \
                            src_fmt in self.src_dest_fmt_to_handling_obj, \
                            "src_fmt {} not supported yet.".format(src_fmt), \
                                                                    __file__)
        ERROR_HANDLER.assert_true( \
                    src_fmt in self.src_dest_fmt_to_handling_obj[src_fmt], \
                    "dest_fmt {} not supported yet for src_fmt {}.".format( \
                                                dest_fmt, src_fmt), __file__)
        
        # call handler
        handler = self.src_dest_fmt_to_handling_obj[src_fmt][dest_fmt]
        ret = handler.convert_code(src_fmt, dest_fmt, \
                            src_dest_files_paths_map, \
                            repository_manager=self.repository_manager)
        return ret
    #~ def transform_src_into_dest ()
    
    def override_registration (self, src_fmt, dest_fmt, handling_obj):
        """set another obj to handle src dest pair or a new one
        """
        # invalidate existing
        if src_fmt in self.src_dest_fmt_to_handling_obj:
            if dest_fmt in self.src_dest_fmt_to_handling_obj[src_fmt]:
                del self.src_dest_fmt_to_handling_obj[src_fmt][dest_fmt]

        # register
        self._fmt_from_to_registration(src_fmt, dest_fmt, handling_obj)
    #~ def override_registration ()
#~ class CodeBuildsFactory()