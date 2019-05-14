
from __future__ import print_function

import os
import sys
import logging
import shutil
import abc

import muteria.common.mix as common_mix

from muteria.repositoryandcode.callback_object import DefaultCallbackObject

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
    def convert_code(self, src_fmt, dest_fmt, file_src_dest_map, \
                                                repository_manager, **kwargs):
        pass

    @abc.abstractmethod
    def get_source_formats(self):
        pass

    @abc.abstractmethod
    def get_destination_formats_for(self, src_fmt):
        pass
#~ class BaseCodeFormatConverter

class IdentityCodeConverter(BaseCodeFormatConverter):

    class CopyCallbackObject(DefaultCallbackObject):
        def after_command(self):
            file_src_dest_map = self.post_callback_args
            for src, dest in list(file_src_dest_map.items()):
                abs_src = os.path.join(self.repository_rootdir, src)
                if os.path.abspath(abs_src) != os.path.abspath(dest):
                    shutil.copy2(src, dest)
            return DefaultCallbackObject.after_command(self)
        #~ def after_command()
    #~ class CopyCallbackObject

    def convert_code(self, src_fmt, dest_fmt, file_src_dest_map, \
                                                repository_manager, **kwargs):
        # make sure that different sources have different destinations
        ERROR_HANDLER.assert_true(len(file_src_dest_map) == \
                    len({file_src_dest_map[fn] for fn in file_src_dest_map}), \
                        "Must specify one destination for each file", __file__)
        # copy the sources into the destinations
        copy_callback_obj = self.CopyCallbackObject()
        copy_callback_obj.set_post_callback_args(file_src_dest_map)
        b_ret, a_ret = repository_manager.custom_read_access(copy_callback_obj)
        ERROR_HANDLER.assert_true(b_ret & a_ret, "code copy failed", __file__)
        return True
    #~ def identity_function()

    def get_source_formats(self):
        ERROR_HANDLER.error_exit(\
                    "get_source_formats must not be called here", __file__)
    #~ def get_source_formats()

    def get_destination_formats_for(self, src_fmt):
        ERROR_HANDLER.error_exit(\
                "get_destination_formats must not be called here", __file__)
    #~ def get_destination_formats()
#~ class IdentityCodeConverter