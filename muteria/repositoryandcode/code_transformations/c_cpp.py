
from __future__ import print_function

import sys
import os
import logging
import shutil

import muteria.common.mix as common_mix

import muteria.repositoryandcode.codes_convert_support as ccs
from muteria.repositoryandcode.callback_object import DefaultCallbackObject
from muteria.drivers import DriversUtils

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
            # XXX: This build overrides passed clean_tmp and reconfigure
            # also overrides Compiler if wllvm if found
            # and does not use the callback object
            # and require file_src_dest_map to have the place to store
            # generated .bc by specifying the corresponding native file.
            # EX: {x.c: /path/to/main} passed to have /path/to/main.bc
            # generated

            spec_compiler = kwargs['compiler'] if 'compiler' in kwargs \
                                                                    else None
            # special kwargs
            spec_llvm_compiler_path = None 
            if 'llvm_compiler_path' in kwargs:
                spec_llvm_compiler_path = kwargs['llvm_compiler_path']
                del kwargs['llvm_compiler_path']

            # If an llvm compiler is specified, 
            # use it instead of the WLLVM default
            if spec_compiler is not None:
                if 'LLVM_COMPILER' not in os.environ:
                    bak_llvm_compiler = None
                else:
                    bak_llvm_compiler = os.environ['LLVM_COMPILER']
                os.environ['LLVM_COMPILER'] = spec_compiler
            else:
                if 'LLVM_COMPILER' not in os.environ:
                    # default to clang
                    os.environ['LLVM_COMPILER'] = 'clang'

            if spec_llvm_compiler_path is not None:
                if 'LLVM_COMPILER_PATH' not in os.environ:
                    bak_llvm_compiler_path = None
                else:
                    bak_llvm_compiler_path = os.environ['LLVM_COMPILER_PATH']
                os.environ['LLVM_COMPILER_PATH'] = spec_llvm_compiler_path

            #1. Ensure wllvm is installed (For now use default llvm compiler)
            has_wllvm = DriversUtils.check_tool('wllvm', ['--version'])
            ERROR_HANDLER.assert_true(has_wllvm, 'wllvm not found '\
                                                '(To install please visit '\
                            'https://github.com/travitch/whole-program-llvm)', 
                                                                    __file__)

            # tmp['LLVM_COMPILER_PATH'] = ...
            kwargs['compiler'] = 'wllvm'
            kwargs['clean_tmp'] = True
            kwargs['reconfigure'] = True

            # Normal build followed by executable copying
            pre_ret, ret, post_ret = repository_manager.build_code(**kwargs)
            ERROR_HANDLER.assert_true(\
                    ret != common_mix.GlobalConstants.COMMAND_FAILURE and\
                    pre_ret != common_mix.GlobalConstants.COMMAND_FAILURE and\
                    post_ret != common_mix.GlobalConstants.COMMAND_FAILURE,\
                                        "Build LLVM bitcode failed!", __file__)

            # extract bitcode from copied executables and remove non bitcode
            # TODO: make this happen as post callback of compilation with wllvm
            if file_src_dest_map is not None:
                for src, dest in list(file_src_dest_map.items()):
                    ret, out, err = \
                            DriversUtils.execute_and_get_retcode_out_err( \
                                                        "extract-bc", [dest])
                    ERROR_HANDLER.assert_true(ret == 0, \
                                        '{}. \n# OUT: {}\n# ERR: {}'.format(\
                                    'extract-bc failed', out, err), __file__)
                    os.remove(dest)

            if spec_compiler is not None:
                if bak_llvm_compiler is not None:
                    os.environ['LLVM_COMPILER'] = bak_llvm_compiler
                else:
                    del os.environ['LLVM_COMPILER']
            if spec_llvm_compiler_path is not None:
                if bak_llvm_compiler_path is not None:
                    os.environ['LLVM_COMPILER_PATH'] = bak_llvm_compiler_path
                else:
                    del os.environ['LLVM_COMPILER_PATH']

            # Clean build
            kwargs['compiler'] = None
            pre_ret, ret, post_ret = repository_manager.build_code(**kwargs)

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
