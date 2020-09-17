
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
from muteria.drivers.testgeneration.testcase_formats.ktest.utils \
                                         import ConvertCollectKtestsSeeds, Misc
from muteria.drivers.testgeneration.tools_by_languages.c.klee.driver_config \
                                                        import DriverConfigKlee

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesToolKlee(BaseTestcaseTool):

    SEED_DIR_ARG_NAME = 'seed-out-dir' #Newer klee is #'seed-dir'

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

        self.driver_config = None
        if self.config.get_tool_user_custom() is not None:
            self.driver_config = \
                            self.config.get_tool_user_custom().DRIVER_CONFIG
        if self.driver_config is None:
            self.driver_config = DriverConfigKlee()
        else:
            ERROR_HANDLER.assert_true(isinstance(self.driver_config, \
                                        DriverConfigKlee),\
                                            "invalid driver config", __file__)

        self.test_details_file = \
                    os.path.join(self.tests_working_dir, 'test_details.json')
        self.klee_used_tmp_build_dir = os.path.join(self.tests_working_dir, \
                                    self._get_tool_name()+'_used_tmp_build_dir')

        # mapping between exes, to have a local copy for execution
        self.repo_exe_to_local_to_remote = {}

        self.keptktest2dupktests = os.path.join(self.tests_working_dir, \
                                                'kept_to_dup_ktests_map.json')
        
        self.ktest_with_must_exist_dir_file = os.path.join(\
                                                self.tests_storage_dir, \
                                                'ktest_to_must_exist_dir.json')
        if os.path.isfile(self.ktest_with_must_exist_dir_file):
            self.ktest_with_must_exist_dir = common_fs.loadJSON(\
                                          self.ktest_with_must_exist_dir_file)
        else:
            self.ktest_with_must_exist_dir = {}

        self.gen_tests_no_dup_with_seeds = \
                        self.driver_config.get_gen_tests_no_dup_with_seeds ()

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
            '-'+self.SEED_DIR_ARG_NAME: None, 
        }
        return bool_params, key_val_params
    #~ def _get_default_params()
    
    @staticmethod
    def _validate_passed_sym_args(raw_sym_args):
        """ check that the sym args are properly formated
        """
        pb = []
        for g in raw_sym_args:
            if type(g) not in (list, tuple):
                pb.append(g)
            else:
                for elem in g:
                    if type(elem) != str or ' ' in elem:
                        pb.append(g)
        ERROR_HANDLER.assert_true(len(pb) == 0, \
                "There are missformed passed sym args: {}".format(pb), \
                                                                __file__)
    #~ def _validate_passed_sym_args()
    
    # SHADOW override
    def _get_sym_args(self, cfg_args):
        # sym args
        default_sym_args = ['-sym-arg', '5']

        klee_sym_args = None
        uc = self.config.get_tool_user_custom()
        if uc is not None:
            post_bc_cmd = uc.POST_TARGET_CMD_ORDERED_FLAGS_LIST
            if post_bc_cmd is not None:
                self._validate_passed_sym_args(post_bc_cmd)
                klee_sym_args = []
                for tup in post_bc_cmd:
                    klee_sym_args += list(tup)

        # Use seeds's (merge with the specified insdead of override)            
        seed_dir = self.get_value_in_arglist(cfg_args, self.SEED_DIR_ARG_NAME)
        if seed_dir is not None:
            cv = ConvertCollectKtestsSeeds(\
                                    custom_binary_dir=self.custom_binary_dir)
            grouped_klee_sym_args = cv.get_ktests_sym_args(seed_dir, \
                                        compressed=seed_dir.endswith(\
                                            ConvertCollectKtestsSeeds.tar_gz))
            self._validate_passed_sym_args(grouped_klee_sym_args)
            klee_sym_args = []
            for tup in grouped_klee_sym_args:
                klee_sym_args += list(tup)

        if klee_sym_args is None:
            klee_sym_args = default_sym_args

        
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

    # SEMu may override
    def _get_compile_flags_list(self):
        return None
    #~ def _get_compile_flags_list()

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
        #to give time to klee add FRAMEWORK GRACE
        max_time = cur_max_time + \
                                self.config.TEST_GEN_TIMEOUT_FRAMEWORK_GRACE

        # set stack to unlimited
        stack_ulimit_soft, stack_ulimit_hard = \
                                    resource.getrlimit(resource.RLIMIT_STACK)
        if stack_ulimit_soft != -1:
            resource.setrlimit(resource.RLIMIT_STACK, (-1, stack_ulimit_hard))

        # Execute Klee
        if self.driver_config.get_suppress_generation_stdout():
            ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                    runtool, args_list=args, timeout=max_time,\
                                    timeout_grace_period=timeout_grace_period, \
                                    out_on=False, err_on=True, \
                                    merge_err_to_out=False)
            out, err = err, out
        else:
            ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                    runtool, args_list=args, timeout=max_time,\
                                    timeout_grace_period=timeout_grace_period)
                                    #out_on=False, err_on=False)
        '''o_d_dbg = self.get_value_in_arglist(args, "output-dir") #DBG
        if os.path.isdir(o_d_dbg): #DBG
            shutil.rmtree(o_d_dbg) #DBG
        import subprocess #DBG
        p = subprocess.Popen([runtool]+args, env=None, cwd=None, \
                                                            #close_fds=True, \
                                                        stdin=None, \
                                                        stderr=subprocess.STDOUT, \
                                                        stdout=None, shell=True, \
                                                        preexec_fn=os.setsid) #DBG
        try: #DBG
            stdout, stderr = p.communicate(timeout=max_time) #DBG
        except subprocess.TimeoutExpired: #DBG
            stdout, stderr = p.communicate(timeout=max_time) #DBG
        #os.system(" ".join([runtool]+args)) #DBG'''
         
        # restore stack
        if stack_ulimit_soft != -1:
            resource.setrlimit(resource.RLIMIT_STACK, \
                                        (stack_ulimit_soft, stack_ulimit_hard))

        if (ret != 0 and ret not in DriversUtils.EXEC_TIMED_OUT_RET_CODE \
                and not out.rstrip().endswith(": ctrl-c detected, exiting.")):
            logging.error(out)
            logging.error(err)
            logging.error("\n>> CMD: " + " ".join([runtool]+args) + '\n')
            ERROR_HANDLER.error_exit("call to klee testgen failed, "
                                    + "error code is {}".format(ret), __file__)
        
        if self.driver_config.get_verbose_generation():
            logging.debug(out)
            logging.debug(err)
            logging.debug("\nCMD: " + " ".join([runtool]+args))
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
        compile_flags_list = self._get_compile_flags_list()
        
        pre_ret, ret, post_ret = code_builds_factory.transform_src_into_dest(\
                        src_fmt=CodeFormats.C_SOURCE,\
                        dest_fmt=CodeFormats.LLVM_BITCODE,\
                        src_dest_files_paths_map=rel_path_map,\
                        compiler=back_llvm_compiler, \
                        llvm_compiler_path=back_llvm_compiler_path, \
                        clean_tmp=True, reconfigure=True, \
                        flags_list=compile_flags_list)
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
                        gen_time = self._get_generation_time_of_test(tc, \
                                                     self.tests_storage_dir)
                        tc_info_obj.add_test(tc, generation_time=gen_time)
            os.chdir(cwd)
            self.testcase_info_object = tc_info_obj
            return self.testcase_info_object
    #~ def get_testcase_info_object()
    
    @staticmethod
    def _get_generation_time_of_test(test, test_top_dir):
        """ extract the generation timestamp of a test. the test and 
            its top location are specified
        """
        # FIXME: implememnt this in klee
        return None
    #~ def _get_generation_time_of_test()

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

        # get stdin if exists
        stdin_file = os.path.join(self.tests_storage_dir, \
                                        os.path.dirname(testcase), \
                                        KTestTestFormat.STDIN_KTEST_DATA_FILE)
        if os.path.isfile(stdin_file) and os.path.getsize(stdin_file) > 0:
            stdin = open(stdin_file)
        else:
            stdin = None

        if testcase in self.ktest_with_must_exist_dir and \
                      len(self.ktest_with_must_exist_dir[testcase]) > 0:
            must_exist_dirs = self.ktest_with_must_exist_dir[testcase]
        else:
            must_exist_dirs = None
        
        verdict = KTestTestFormat.execute_test(local_exe, \
                        os.path.join(self.tests_storage_dir, testcase), \
                        env_vars=env_vars, \
                        stdin=stdin, \
                        must_exist_dir_list=must_exist_dirs, \
                        timeout=timeout, \
                        collected_output=collected_output, \
                        custom_replay_tool_binary_dir=self.custom_binary_dir)
        
        if stdin is not None:
            stdin.close()

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
                    bool_disabled = False
                    if key in k_v_params:
                        del k_v_params[key]
                    if key in bool_param:
                        del bool_param[key]
                        if len(tup) == 2:
                            ERROR_HANDLER.assert_true(\
                                        type(tup[1]) == bool, \
                                        "bool arg is either enabled or "
                                    "disabled. val must be bool", __file__)
                            if not tup[1]:
                                bool_disabled = True
                            tup = tup[:1]
                        else:
                            ERROR_HANDLER.assert_true(len(tup) == 1, \
                                    "Invalid bool param: "+key, __file__)
                    if not bool_disabled:
                        pre_args.extend(list(tup))

        args = [bp for bp, en in list(bool_param.items()) if en]
        for k,v in list(k_v_params.items()):
            if v is not None:
                args += [k,str(v)]
        args.extend(pre_args)

        args.append(bitcode_file)

        args += self._get_sym_args(args)

        self._call_generation_run(prog, list(args))

        # XXX: remove duplicate tests
        kepttest2duptest_map = {}
        folders = [self.tests_storage_dir]
        if self.gen_tests_no_dup_with_seeds:
            seed_dir = self.get_value_in_arglist(args, self.SEED_DIR_ARG_NAME)
            if seed_dir is not None:
                seed_dir = os.path.normpath(os.path.abspath(seed_dir))
                folders.append(seed_dir)

        dup_list, invalid = KTestTestFormat.ktest_fdupes(*folders, \
                        custom_replay_tool_binary_dir=self.custom_binary_dir)
        if len(invalid) > 0:
            logging.warning(\
                        "{} generated ktests are invalid ({})".format(\
                                                        len(invalid), invalid))
            for kt in invalid:
                if KTestTestFormat.get_dir(kt, folders) == \
                                                        self.tests_storage_dir:
                    os.remove(kt)
        for dup_tuple in dup_list:
            key = os.path.relpath(dup_tuple[0], \
                                KTestTestFormat.get_dir(dup_tuple[0], folders))
            kepttest2duptest_map[key] = [os.path.relpath(dp, \
                                        KTestTestFormat.get_dir(dp, folders)) \
                                                for dp in dup_tuple[1:]]
            for df in dup_tuple[1:]:
                if KTestTestFormat.get_dir(df, folders) == \
                                                        self.tests_storage_dir:
                    os.remove(df)
        common_fs.dumpJSON(kepttest2duptest_map, self.keptktest2dupktests)
        
        # Copy replay tool into test folder
        klee_replay_pathname = KTestTestFormat.get_test_replay_tool(\
                        custom_replay_tool_binary_dir=self.custom_binary_dir)
        shutil.copy2(klee_replay_pathname, self.tests_storage_dir)

        store_obj = {repo_rel_exe_file: os.path.basename(bitcode_file)}
        common_fs.dumpJSON(store_obj, self.test_details_file)
        
        # Compute must exist dirs
        test2file = {}
        for kt in self.get_testcase_info_object().get_tests_list():
            test2file[kt] = os.path.join(self.tests_storage_dir, kt)
        ktest2reqdir = Misc.get_must_exist_dirs_of_ktests(test2file, \
                                                    self.custom_binary_dir)
        ktest2reqdir = {kt: v for kt, v in ktest2reqdir.items() if len(v) > 0}
        self.ktest_with_must_exist_dir = ktest2reqdir
        if len(ktest2reqdir) > 0:
            common_fs.dumpJSON(ktest2reqdir, \
                                        self.ktest_with_must_exist_dir_file)
    #~ def _do_generate_tests()

    def get_ktests_dir(self):
        return self.tests_storage_dir
    #~ def get_ktests_dir()

    def can_run_tests_in_parallel(self):
        return True
    #~ def can_run_tests_in_parallel()

    def get_test_format_class (self):
        return KTestTestFormat
    # def get_test_format_class ()
#~ class TestcasesToolKlee
