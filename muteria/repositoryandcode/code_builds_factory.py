"""
"""

from __future__ import print_function

import sys
import os
import logging
import shutil

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

import muteria.repositoryandcode.code_transformations as ct_modules
import muteria.repositoryandcode.codes_convert_support as ccs

from muteria.repositoryandcode.callback_object import DefaultCallbackObject

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

    # From Python source
    (ccs.CodeFormats.PYTHON_SOURCE, ccs.IdentityCodeConverter()),
]

class CodeBuildsFactory(object):
    def __init__(self, repository_manager, workdir=None):
        self.repository_manager = repository_manager
        self.workdir = workdir
        self.src_dest_fmt_to_handling_obj = {}

        self.stored_files_mapping = None
        self.stored_files_mapping_file = None
        if self.workdir is not None:
            self.stored_files_mapping_file = \
                                        os.path.join(self.workdir, "files_map")
            exes, src_obj_map = \
                            self.repository_manager.get_relative_exe_path_map()
            if os.path.isdir(self.workdir):
                self.stored_files_mapping = \
                            common_fs.loadJSON(self.stored_files_mapping_file)
            else:
                os.mkdir(self.workdir)
                count = 0
                self.stored_files_mapping = {}
                for f in exes:
                    self.stored_files_mapping[f] = \
                                        os.path.join(self.workdir, str(count))
                    count += 1
                for s,o in list(src_obj_map.items()):
                    self.stored_files_mapping[o] = \
                                        os.path.join(self.workdir, str(count))
                    count += 1
                common_fs.dumpJSON(self.stored_files_mapping, \
                                self.stored_files_mapping_file, pretty=True)
        
        # Initialize 
        for src_fmt, obj_cls in formatfrom_function_tuples:
            if isinstance(obj_cls, ccs.IdentityCodeConverter):
                self._fmt_from_to_registration(src_fmt, src_fmt, obj_cls)
            else:
                ERROR_HANDLER.assert_true(\
                                src_fmt in obj_cls.get_source_formats(), \
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
                    dest_fmt in self.src_dest_fmt_to_handling_obj[src_fmt], \
                    "dest_fmt {} not supported yet for src_fmt {}.".format( \
                                                dest_fmt, src_fmt), __file__)
        
        # call handler
        handler = self.src_dest_fmt_to_handling_obj[src_fmt][dest_fmt]
        pre_ret, ret, post_ret = handler.convert_code(src_fmt, dest_fmt, \
                            src_dest_files_paths_map, \
                            repository_manager=self.repository_manager, \
                            **kwargs)
        return pre_ret, ret, post_ret
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

    ## Useful
    
    class CopyCallbackObject(DefaultCallbackObject):
        def before_command(self):
            revert_src_func = self.pre_callback_args
            revert_src_func()
            return common_mix.GlobalConstants.COMMAND_SUCCESS
        #~ def before_command()

        def after_command(self):
            if self.op_retval == common_mix.GlobalConstants.COMMAND_FAILURE:
                return common_mix.GlobalConstants.COMMAND_FAILURE
            file_src_dest_map, reverse = self.post_callback_args
            if reverse:
                self._copy_to_repo(file_src_dest_map)
            else:
                self._copy_from_repo(file_src_dest_map)
            return common_mix.GlobalConstants.COMMAND_SUCCESS
        #~ def after_command()
    #~ class CopyCallbackObject

    def set_repo_to_build_default(self):
        if self.repository_manager.should_build():
            files_backed = False
            if self.stored_files_mapping is not None and \
                                            len(self.stored_files_mapping) > 0:
                files_backed = os.path.isfile(\
                                    self.stored_files_mapping[\
                                    list(self.stored_files_mapping.keys())[0]])

                # copy the sources into the destinations
                copy_callback_obj = self.CopyCallbackObject()
                copy_callback_obj.set_pre_callback_args( \
                                self.repository_manager.revert_src_list_files)

            if files_backed:
                copy_callback_obj.set_post_callback_args(\
                                            [self.stored_files_mapping, True])
                b_ret, a_ret = self.repository_manager.custom_read_access(\
                                                            copy_callback_obj)
                ERROR_HANDLER.assert_true(\
                        b_ret == common_mix.GlobalConstants.COMMAND_SUCCESS & \
                        a_ret == common_mix.GlobalConstants.COMMAND_SUCCESS, \
                                                "code copy failed", __file__)
            else:
                # build and possibly backup
                if self.stored_files_mapping is None:
                    co = None
                else:
                    copy_callback_obj.set_post_callback_args(\
                                            [self.stored_files_mapping, False])
                    co = copy_callback_obj
                pre, ret, post = self.repository_manager.build_code(
                                                            clean_tmp=True, \
                                                            reconfigure=True, \
                                                            callback_object=co)
                if pre == common_mix.GlobalConstants.COMMAND_FAILURE or \
                        ret == common_mix.GlobalConstants.COMMAND_FAILURE or \
                        post == common_mix.GlobalConstants.COMMAND_FAILURE:
                    ERROR_HANDLER.error_exit("default build failed", __file__)
    #~ def set_repo_to_build_default(self)
#~ class CodeBuildsFactory()