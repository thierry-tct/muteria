
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import resource

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.drivers.testgeneration.base_testcasetool import BaseTestcaseTool
from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject
from muteria.drivers import DriversUtils
from muteria.drivers.testgeneration.testcase_formats.ktest.ktest \
                                                        import KTestTestFormat

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesToolKlee(BaseTestcaseTool):

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        for prog in ('klee',):
            if custom_binary_dir is not None:
                prog = os.path.join(custom_binary_dir, prog)
            if not DriversUtils.check_tool(prog=prog, args_list=['--version'],\
                                                    expected_exit_codes=[0,1]):
                return False

        return KTestTestFormat.installed(custom_binary_dir=custom_binary_dir)
    #~ def installed()

    def __init__(self, *args, **kwargs):
        BaseTestcaseTool.__init__(self, *args, **kwargs)
        self.test_details_file = \
                    os.path.join(self.tests_working_dir, 'test_details.json')
        self.klee_used_tmp_build_dir = os.path.join(self.tests_working_dir, \
                                    self._get_tool_name()+'_used_tmp_build_dir')

        # mapping between exes, to have a local copy for execution
        self.repo_exe_to_local_to_remote = {}

        self.keptktest2dupktests = os.path.join(self.tests_working_dir, \
                                                'kept_to_dup_ktests_map.json')

        if os.path.isdir(self.klee_used_tmp_build_dir):
            shutil.rmtree(self.klee_used_tmp_build_dir)
        os.mkdir(self.klee_used_tmp_build_dir)
    #~ def __init__()

    # SHADOW override
    def _get_default_params(self):
        bool_params = {
            '-ignore-solver-failures': None,
            '-allow-external-sym-calls': True, #None,
            '-posix-runtime': True, #None,
            '-dump-states-on-halt': True, #None,
            '-only-output-states-covering-new': True,
            '-use-cex-cache': True,
        }
        key_val_params = {
            '-output-dir': self.tests_storage_dir,
            '-solver-backend': None,
            '-max-solver-time': None,
            '-search': None,
            '-max-memory': None,
            '-max-time': self.config.TEST_GENERATION_MAXTIME,
            '-libc': 'uclibc',
            '-max-sym-array-size': '4096',
            '-max-instruction-time': '10.',
        }
        return bool_params, key_val_params
    #~ def _get_default_params()
    
    # SHADOW override
    def _get_sym_args(self):
        # sym args
        default_sym_args = ['-sym-arg', '5']

        klee_sym_args = default_sym_args
        uc = self.config.get_tool_user_custom()
        if uc is not None:
            post_bc_cmd = uc.POST_TARGET_CMD_ORDERED_FLAGS_LIST
            if post_bc_cmd is not None:
                klee_sym_args = []
                for tup in post_bc_cmd:
                    klee_sym_args += list(tup)
        return klee_sym_args
    #~ def _get_sym_args()

    # SHADOW should override
    def _get_back_llvm_compiler(self):
        return None #'clang'
    #~ def _get_back_llvm_compiler()

    # SHADOW should override
    def _get_back_llvm_compiler_path(self):
        return None 
    #~ def _get_back_llvm_compiler_path()

    @staticmethod
    def get_value_in_arglist(arglist, flagname):
        value = None
        for i, v in enumerate(arglist):
            if v in ('-'+flagname, '--'+flagname):
                value = arglist[i+1]
                break
            elif v.startswith('-'+flagname+'=') \
                                            or v.startswith('--'+flagname+'='):
                _, value = v.split('=')
                break
        return value
    #~ def get_value_in_arglist()

    @staticmethod
    def set_value_in_arglist(arglist, flagname, value):
        for i, v in enumerate(arglist):
            if v in ('-'+flagname, '--'+flagname):
                arglist[i+1] = value
                break
            elif v.startswith('-'+flagname+'=') \
                                            or v.startswith('--'+flagname+'='):
                pre, _ = v.split('=')
                arglist[i] = pre + '=' + str(value)
                break
    #~ def set_value_in_arglist()

    @staticmethod
    def remove_arg_and_value_from_arglist(arglist, flagname):
        for i, v in enumerate(arglist):
            if v in ('-'+flagname, '--'+flagname):
                del arglist[i+1]
                del arglist[i]
                break
            elif v.startswith('-'+flagname+'=') \
                                            or v.startswith('--'+flagname+'='):
                del arglist[i]
                break
    #~ def remove_arg_and_value_from_arglist()

    # SHADOW should override
    def _call_generation_run(self, runtool, args):
        ## locate max-time
        timeout_grace_period = 600
        max_time = None
        cur_max_time = float(self.get_value_in_arglist(args, 'max-time'))
        max_time = cur_max_time + 5 #5 to give time to klee

        # set stack to unlimited
        stack_ulimit_soft, stack_ulimit_hard = \
                                    resource.getrlimit(resource.RLIMIT_STACK)
        if stack_ulimit_soft != -1:
            resource.setrlimit(resource.RLIMIT_STACK, (-1, stack_ulimit_hard))

        # Execute Klee
        ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                    runtool, args, timeout=max_time, \
                                    timeout_grace_period=timeout_grace_period)
                                    #out_on=False, err_on=False)
        
        # restore stack
        if stack_ulimit_soft != -1:
            resource.setrlimit(resource.RLIMIT_STACK, \
                                        (stack_ulimit_soft, stack_ulimit_hard))

        if (ret != 0 and ret not in DriversUtils.EXEC_TIMED_OUT_RET_CODE):
            logging.error(out)
            logging.error(err)
            logging.error("\n>> CMD: " + " ".join([runtool]+args) + '\n')
            ERROR_HANDLER.error_exit("call to klee testgen failed, "
                                    + "error code is {}".format(ret), __file__)
    #~ def _call_generation_run()

    # SHADOW should override
    def _get_testexec_extra_env_vars(self, testcase):
        return None
    #~ def _get_testexec_extra_env_vars()
    
    def _get_tool_name(self):
        return 'klee'
    #~ def _get_tool_name()

    def _get_input_bitcode_file(self, code_builds_factory, rel_path_map, \
                                                meta_criteria_tool_obj=None):
        back_llvm_compiler = self._get_back_llvm_compiler() 
        back_llvm_compiler_path = self._get_back_llvm_compiler_path() 
        
        pre_ret, ret, post_ret = code_builds_factory.transform_src_into_dest(\
                        src_fmt=CodeFormats.C_SOURCE,\
                        dest_fmt=CodeFormats.LLVM_BITCODE,\
                        src_dest_files_paths_map=rel_path_map,\
                        compiler=back_llvm_compiler, \
                        llvm_compiler_path=back_llvm_compiler_path, \
                        clean_tmp=True, reconfigure=True)
        if ret == common_mix.GlobalConstants.COMMAND_FAILURE:
            ERROR_HANDLER.error_exit("Program {}.".format(\
                                        'LLVM built problematic'), __file__)

        # Update exe_map to reflect bitcode extension
        rel2bitcode = {}
        for r_file, b_file in list(rel_path_map.items()):
            bc = b_file+'.bc'
            ERROR_HANDLER.assert_true(os.path.isfile(bc), \
                                    "Bitcode file not existing: "+bc, __file__)
            rel2bitcode[r_file] = bc

        ERROR_HANDLER.assert_true(len(rel_path_map) == 1, \
                            "Support single bitcode module for now", __file__)

        bitcode_file = rel2bitcode[list(rel2bitcode.keys())[0]]
        return bitcode_file
    #~ def _get_input_bitcode_file()
    ########################################################################

    def get_testcase_info_object(self):
        try:
            return self.testcase_info_object
        except AttributeError:
            tc_info_obj = TestcasesInfoObject()
            cwd = os.getcwd()
            os.chdir(self.tests_storage_dir)
            for root, _, files in os.walk('.'):
                for f in files:
                    tc = os.path.normpath(os.path.join(root, f))
                    if tc.endswith(KTestTestFormat.ktest_extension):
                        tc_info_obj.add_test(tc)
            os.chdir(cwd)
            self.testcase_info_object = tc_info_obj
            return self.testcase_info_object
    #~ def get_testcase_info_object()

    def _prepare_executable(self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Make sure we have the right executable ready (if needed)
        """
        #self.code_builds_factory.copy_into_repository(exe_path_map)
        pass
    #~ def _prepare_executable()

    def _restore_default_executable(self, exe_path_map, env_vars, \
                                                        collect_output=False):
        """ Restore back the default executable (if needed).
            Useful for test execution that require the executable
            at a specific location.
        """
        #self.code_builds_factory.restore_repository_files(exe_path_map)
        pass
    #~ def _restore_default_executable()

    def _execute_a_test (self, testcase, exe_path_map, env_vars, \
                    callback_object=None, timeout=None, collect_output=False):
        """ Execute a test given that the executables have been set 
            properly
        """

        if timeout is None:
            timeout = self.config.ONE_TEST_EXECUTION_TIMEOUT
        
        #logging.debug('TIMEOUT: '+str(timeout))

        ERROR_HANDLER.assert_true(len(exe_path_map) == 1, \
                                    "support a single exe for now", __file__)
        ERROR_HANDLER.assert_true(callback_object is None, \
                                        'TODO: handle callback_obj', __file__)
        
        repo_exe = list(exe_path_map.keys())[0]
        local_exe = os.path.join(self.klee_used_tmp_build_dir, repo_exe)
        if repo_exe not in self.repo_exe_to_local_to_remote:
            with self.shared_loc:
                if repo_exe not in self.repo_exe_to_local_to_remote:
                    if not os.path.isdir(os.path.dirname(local_exe)):
                        os.makedirs(os.path.dirname(local_exe))
                    self.repo_exe_to_local_to_remote[repo_exe] = \
                                                            {local_exe: None}

        remote_exe = exe_path_map[repo_exe]
        if remote_exe is None:
            remote_exe = repo_exe

        if remote_exe != self.repo_exe_to_local_to_remote[repo_exe][local_exe]:
            with self.shared_loc:
                if remote_exe != \
                        self.repo_exe_to_local_to_remote[repo_exe][local_exe]:
                    if remote_exe == repo_exe:
                        self.code_builds_factory.set_repo_to_build_default(\
                                        also_copy_to_map={repo_exe: local_exe})
                    else:
                        shutil.copy2(remote_exe, local_exe)
                        # Use hard link to avoid copying for big files
                        #if os.path.isfile(local_exe):
                        #    os.remove(local_exe)
                        #os.link(remote_exe, local_exe)
                    self.repo_exe_to_local_to_remote[repo_exe][local_exe] = \
                                                                    remote_exe

        collected_output = [] if collect_output else None

        extra_env = self._get_testexec_extra_env_vars(testcase)
        if extra_env is not None and len(extra_env) > 0:
            env_vars = dict(env_vars).update(extra_env)

        verdict = KTestTestFormat.execute_test(local_exe, \
                        os.path.join(self.tests_storage_dir, testcase), \
                        env_vars=env_vars, \
                        timeout=timeout, \
                        collected_output=collected_output, \
                        custom_replay_tool_binary_dir=self.custom_binary_dir)

        return verdict, collected_output
    #~ def _execute_a_test()

    def _do_generate_tests (self, exe_path_map, code_builds_factory, \
                                                meta_criteria_tool_obj=None, \
                                                                max_time=None):
        # Check the passed exe_path_map
        if exe_path_map is not None:
            for r_exe, v_exe in exe_path_map.items():
                ERROR_HANDLER.assert_true(v_exe is None, \
                            "Klee driver does not use passed exe_path_map", \
                                                                    __file__)

        # Setup
        if os.path.isdir(self.tests_working_dir):
            try:
                shutil.rmtree(self.tests_working_dir)
            except PermissionError:
                self._dir_chmod777(self.tests_working_dir)
                shutil.rmtree(self.tests_working_dir)

        os.mkdir(self.tests_working_dir)
        if os.path.isdir(self.tests_storage_dir):
            shutil.rmtree(self.tests_storage_dir)
        
        prog = self._get_tool_name()
        if self.custom_binary_dir is not None:
            prog = os.path.join(self.custom_binary_dir, prog)
            ERROR_HANDLER.assert_true(os.path.isfile(prog), \
                            "The tool {} is missing from the specified dir {}"\
                                        .format(os.path.basename(prog), \
                                            self.custom_binary_dir), __file__)

        rel_path_map = {}
        exes, _ = code_builds_factory.repository_manager.\
                                                    get_relative_exe_path_map()
        for exe in exes:
            filename = os.path.basename(exe)
            rel_path_map[exe] = os.path.join(self.tests_working_dir, filename)

        # Get bitcode file
        bitcode_file = self._get_input_bitcode_file(code_builds_factory, \
                                                                rel_path_map, \
                                meta_criteria_tool_obj=meta_criteria_tool_obj)
        repo_rel_exe_file = list(rel_path_map)[0]
        
        # klee params
        bool_param, k_v_params = self._get_default_params()
        if max_time is not None:
            k_v_params['-max-time'] = str(max_time)

        # Consider pre user custom
        uc = self.config.get_tool_user_custom()
        pre_args = []
        if uc is not None:
            pre_bc_cmd = uc.PRE_TARGET_CMD_ORDERED_FLAGS_LIST
            if pre_bc_cmd is not None:
                for tup in pre_bc_cmd:
                    key = tup[0][1:] if tup[0].startswith('--') else tup[0]
                    if key in k_v_params:
                        del k_v_params[key]
                    if key in bool_param:
                        del bool_param[key]
                    pre_args.extend(list(tup))

        args = [bp for bp, en in list(bool_param.items()) if en]
        for k,v in list(k_v_params.items()):
            if v is not None:
                args += [k,str(v)]
        args.extend(pre_args)

        args.append(bitcode_file)

        args += self._get_sym_args()

        self._call_generation_run(prog, list(args))

        # XXX: remove duplicate tests
        kepttest2duptest_map = {}
        dup_list, invalid = KTestTestFormat.ktest_fdupes(\
                                                    self.tests_storage_dir, \
                        custom_replay_tool_binary_dir=self.custom_binary_dir)
        if len(invalid) > 0:
            logging.warning(\
                        "{} generated ktests are invalid".format(len(invalid)))
            for kt in invalid:
                os.remove(kt)
        for dup_tuple in dup_list:
            kepttest2duptest_map[os.path.relpath(\
                            dup_tuple[0], \
                            self.tests_storage_dir)] = [os.path.relpath(dp) \
                                                    for dp in dup_tuple[1:]]
            for df in dup_tuple[1:]:
                os.remove(df)
        common_fs.dumpJSON(kepttest2duptest_map, self.keptktest2dupktests)
        
        # Copy replay tool into test folder
        klee_replay_pathname = KTestTestFormat.get_test_replay_tool(\
                        custom_replay_tool_binary_dir=self.custom_binary_dir)
        shutil.copy2(klee_replay_pathname, self.tests_storage_dir)

        store_obj = {repo_rel_exe_file: os.path.basename(bitcode_file)}
        common_fs.dumpJSON(store_obj, self.test_details_file)
    #~ def _do_generate_tests()

    def can_run_tests_in_parallel(self):
        return True
    #~ def can_run_tests_in_parallel()
#~ class TestcasesToolKlee