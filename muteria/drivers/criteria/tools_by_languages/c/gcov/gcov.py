""" TODO: call coverage
"""

from __future__ import print_function

import os
import sys
import re
import shutil
import shlex
import logging
import subprocess

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.repositoryandcode.callback_object import DefaultCallbackObject

from muteria.drivers.criteria.base_testcriteriatool import BaseCriteriaTool
from muteria.drivers.criteria import TestCriteria
from muteria.drivers import DriversUtils

ERROR_HANDLER = common_mix.ErrorHandler

class CriteriaToolGCov(BaseCriteriaTool):
    def __init__(self, *args, **kwargs):
        BaseCriteriaTool.__init__(self, *args, **kwargs)
        self.instrumentation_details = os.path.join(\
                    self.instrumented_code_storage_dir, '.instru.meta.json')
        self.gcov_files_list_filename = "gcov_files.json"
        self.gc_files_dir = os.path.join(\
                                        self.criteria_working_dir, "gcno_gcda")
        self.gcov_gdb_wrapper_template = os.path.join(\
                                                os.path.dirname(__file__), \
                                                'gcov-gdb_call_wrapper.sh.in')
        self.gcov_gdb_wrapper_sh = os.path.join(\
                                        self.instrumented_code_storage_dir, \
                                                    "tmp_gcov_gdb_wrapper.sh")

        # clean any possible gcda file
        for file_ in self._get_gcda_list():
            os.remove(file_)
        for file_ in self._get_gcov_list():
            os.remove(file_)
    #~ def __init__()

    def _get_gcov_list(self):
        gcov_files = []
        for root, dirs, files in os.walk(self.gc_files_dir):
            for file_ in files:
                if file_.endswith('.gcov'):
                    gcov_files.append(os.path.join(root, file_))
        return gcov_files
    #~ def _get_gcov_list()

    def _get_gcda_list(self):
        gcda_files = []
        for root, dirs, files in os.walk(self.gc_files_dir):
            for file_ in files:
                if file_.endswith('.gcda'):
                    gcda_files.append(os.path.join(root, file_))
        return gcda_files
    #~ def _get_gcda_list()

    class InstrumentCallbackObject(DefaultCallbackObject):
        def after_command(self):
            if self.op_retval != common_mix.GlobalConstants.COMMAND_SUCCESS:
                ERROR_HANDLER.error_exit("Build failed", __file__)
            gc_files_dir, rel_path_map = self.post_callback_args
            for _, obj in list(self.source_files_to_objects.items()):
                rel_raw_filename, _ = os.path.splitext(obj)
                gcno_file = rel_raw_filename + '.gcno' 
                relloc = os.path.join(gc_files_dir, os.path.dirname(obj))
                if not os.path.isdir(relloc):
                    os.makedirs(relloc)
                abs_gcno = os.path.join(self.repository_rootdir, gcno_file)
                ERROR_HANDLER.assert_true(os.path.isfile(abs_gcno), \
                                    "gcno file missing after build", __file__)
                shutil.copy2(abs_gcno, os.path.join(gc_files_dir, gcno_file))
            self._copy_from_repo(rel_path_map)
            return DefaultCallbackObject.after_command(self)
        #~ def after_command()
    #~ class InstrumentCallbackObject

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        for prog in ('gcc', 'gcov'):
            if custom_binary_dir is not None:
                prog = os.path.join(custom_binary_dir, prog)
            if not DriversUtils.check_tool(prog=prog, args_list=['--version'],\
                                                    expected_exit_codes=[0]):
                return False
        return True
    #~ def installed()

    @classmethod
    def _get_meta_instrumentation_criteria(cls):
        """ Criteria where all elements are instrumented in same file
            :return: list of citeria
        """
        return [
                TestCriteria.STATEMENT_COVERAGE,
                TestCriteria.BRANCH_COVERAGE,
                TestCriteria.FUNCTION_COVERAGE,
               ]
    #~ def _get_meta_instrumentation_criteria()

    @classmethod
    def _get_separated_instrumentation_criteria(cls):
        """ Criteria where all elements are instrumented in different files
            :return: list of citeria
        """
        return []
    #~ def _get_separated_instrumentation_criteria()

    def get_instrumented_executable_paths_map(self, enabled_criteria):
        # use wrapper if gdb is installed
        using_gdb_wrapper = DriversUtils.check_tool(prog='gdb', \
                                                    args_list=['--version'], \
                                                    expected_exit_codes=[0])
        if using_gdb_wrapper:
            # XXX: Docker has issues running programs in Docker, 
            # unless the container is ran with the following arguments:
            #
            # docker run --cap-add=SYS_PTRACE \
            #               --security-opt seccomp=unconfined ...
            #
            # We check that it is fine by testing on echo
            ret, _, _ = DriversUtils.execute_and_get_retcode_out_err(
                                        prog='gdb', \
                                        args_list=['--batch-silent', \
                                                    '--quiet', 
                                                    '--return-child-result', 
                                                    '-ex', '"run"', 
                                                    '--args', 'echo'], \
                                        out_on=False, err_on=False)
            using_gdb_wrapper = (ret == 0)

        crit_to_exes_map = {}
        obj = common_fs.loadJSON(self.instrumentation_details)
        #exes = [p for _, p in list(obj.items())]
        for name in obj:
            obj[name] = os.path.join(self.instrumented_code_storage_dir, \
                                                                    obj[name])
            
        if using_gdb_wrapper:
            # Using GDB WRAPPER
            with open(self.gcov_gdb_wrapper_template) as f:
                template_str = f.read()
            single_exe = obj[list(obj)[0]]
            template_str = template_str.replace(\
                                'MUTERIA_GCOV_PROGRAMEXE_PATHNAME', single_exe)
            with open(self.gcov_gdb_wrapper_sh, 'w') as f:
                f.write(template_str)
            shutil.copymode(single_exe, self.gcov_gdb_wrapper_sh)
            obj[list(obj)[0]] = self.gcov_gdb_wrapper_sh

        exes_map = obj
        for criterion in enabled_criteria:
            crit_to_exes_map[criterion] = exes_map
        return crit_to_exes_map
    #~ def get_instrumented_executable_paths_map()

    def get_criterion_info_object(self, criterion):
        return None
    #~ def get_criterion_info_object(self, criterion)

    def _get_criterion_element_executable_path(self, criterion, element_id):
        ERROR_HANDLER.error_exit("not applicable for gcov", __file__)
    #~ def _get_criterion_element_executable_path

    def _get_criterion_element_environment_vars(self, criterion, element_id):
        '''
            return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        ERROR_HANDLER.error_exit("not applicable for gcov", __file__)
    #~ def _get_criterion_element_environment_vars()

    def _get_criteria_environment_vars(self, result_dir_tmp, enabled_criteria):
        '''
        return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        return {e:None for e in enabled_criteria}
    #~ def _get_criteria_environment_vars()

    def _collect_temporary_coverage_data(self, criteria_name_list, \
                                            test_execution_verdict, \
                                            used_environment_vars, \
                                            result_dir_tmp, \
                                            testcase):
        ''' get gcov files from gcda files into result_dir_tmp
        '''
        prog = 'gcov'
        if self.custom_binary_dir is not None:
            prog = os.path.join(self.custom_binary_dir, prog)
            ERROR_HANDLER.assert_true(os.path.isfile(prog), \
                            "The tool {} is missing from the specified dir {}"\
                                        .format(os.path.basename(prog), \
                                            self.custom_binary_dir), __file__)

        cov2flags = {
                    TestCriteria.STATEMENT_COVERAGE: [],
                    TestCriteria.BRANCH_COVERAGE: ['-b', '-c'],
                    TestCriteria.FUNCTION_COVERAGE: ['-f'],
                }

        args_list = []
        for criterion in criteria_name_list:
            args_list += cov2flags[criterion]

        gcda_files = self._get_gcda_list()

        raw_filename_list = [os.path.splitext(f)[0] for f in gcda_files]
        args_list += raw_filename_list
        
        if len(gcda_files) > 0:
            # TODO: When gcov generate coverage for different files with
            # same name filename but located at diferent dir. Avoid override.
            # Go where the gcov will be looked for
            cwd = os.getcwd()
            os.chdir(self.gc_files_dir)

            # collect gcda (gcno)
            r, _, _ = DriversUtils.execute_and_get_retcode_out_err(prog=prog, \
                                        args_list=args_list, out_on=False, \
                                                                err_on=False)

            os.chdir(cwd)
            
            if r != 0:
                ERROR_HANDLER.error_exit("Program {} {}.".format(prog,\
                        'error collecting coverage is problematic'), __file__)
            
            # delete gcda
            for gcda_f in gcda_files:
                os.remove(gcda_f)
            
        common_fs.dumpJSON(self._get_gcov_list(), \
                                os.path.join(result_dir_tmp,\
                                                self.gcov_files_list_filename))
        #else:
        #    ERROR_HANDLER.error_exit(\
        #                "Testcase '{}' did not generate gcda".format(testcase))
    #~ def _collect_temporary_coverage_data()

    def _extract_coverage_data_of_a_test(self, enabled_criteria, \
                                    test_execution_verdict, result_dir_tmp):
        ''' read json files and extract data
            return: the dict of criteria with covering count
            # TODO: Restrict to returning coverage of specified headers files
        '''
        gcov_list = common_fs.loadJSON(os.path.join(result_dir_tmp,\
                                                self.gcov_files_list_filename))
        
        res = {c: {} for c in enabled_criteria}

        func_cov = None
        branch_cov = None
        statement_cov = {}
        if TestCriteria.FUNCTION_COVERAGE in enabled_criteria:
            func_cov = res[TestCriteria.FUNCTION_COVERAGE]
        if TestCriteria.BRANCH_COVERAGE in enabled_criteria:
            branch_cov = res[TestCriteria.BRANCH_COVERAGE]
        if TestCriteria.STATEMENT_COVERAGE in enabled_criteria:
            statement_cov = res[TestCriteria.STATEMENT_COVERAGE]

        # Sources of interest
        _, src_map = self.code_builds_factory.repository_manager.\
                                                    get_relative_exe_path_map()

        for gcov_file in gcov_list:
            with open(gcov_file) as fp:
                last_line = None
                src_file = None
                for raw_line in fp:
                    line = raw_line.strip()
                    col_split = [v.strip() for v in line.split(':')]

                    if len(col_split) > 2 and col_split[1] == '0':
                        # preamble
                        if col_split[2] == "Source":
                            src_file = col_split[3]
                            if src_file not in src_map:
                                # src not in considered
                                break
                    elif line.startswith("function "):
                        # match function
                        parts = line.split()
                        ident = DriversUtils.make_meta_element(parts[1], \
                                                                    src_file)
                        func_cov[ident] = int(parts[3])
                    elif line.startswith("branch "):
                        # match branch
                        parts = line.split()
                        ident = DriversUtils.make_meta_element(parts[1], \
                                                                    last_line)
                        if parts[2:4] == ['never', 'executed']:
                            branch_cov[ident] = 0
                        else:
                            branch_cov[ident] = int(parts[3])

                    elif len(col_split) > 2 and \
                                            re.match(r"^\d+$", col_split[1]):
                        # match line
                        if col_split[0] == '-':
                            continue
                        last_line = DriversUtils.make_meta_element(\
                                                        col_split[1], src_file)
                        if col_split[0] in ('#####', '====='):
                            exec_count = 0
                        else:
                            exec_count = \
                                    int(re.findall(r'^\d+', col_split[0])[0])
                        statement_cov[last_line] = exec_count

        # delete gcov files
        for gcov_f in self._get_gcov_list():
            os.remove(gcov_f)

        return res
    #~ def _extract_coverage_data_of_a_test()

    def _do_instrument_code (self, exe_path_map, \
                                        code_builds_factory, \
                                        enabled_criteria, parallel_count=1):
        # Setup
        if os.path.isdir(self.instrumented_code_storage_dir):
            shutil.rmtree(self.instrumented_code_storage_dir)
        os.mkdir(self.instrumented_code_storage_dir)
        if os.path.isdir(self.gc_files_dir):
            try:
                shutil.rmtree(self.gc_files_dir)
            except PermissionError:
                self._dir_chmod777(self.gc_files_dir)
                shutil.rmtree(self.gc_files_dir)
        os.mkdir(self.gc_files_dir, mode=0o777)

        prog = 'gcc'
        if self.custom_binary_dir is not None:
            prog = os.path.join(self.custom_binary_dir, prog)
            ERROR_HANDLER.assert_true(os.path.isfile(prog), \
                            "The tool {} is missing from the specified dir {}"\
                                        .format(os.path.basename(prog), \
                                            self.custom_binary_dir), __file__)

        flags = ['-g', '--coverage', '-fprofile-dir='+self.gc_files_dir, '-O0']
        additionals = ["-fkeep-inline-functions"]
        
        # get gcc version
        ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                                        prog, ['-dumpversion'])
        ERROR_HANDLER.assert_true(ret == 0, "'gcc -dumpversion' failed'")
        
        # if version > 6.5
        if int(out.split('.')[0]) >= 6:
            if int(out.split('.')[0]) > 6 or int(out.split('.')[1]) > 5:
                additionals += ["-fkeep-static-functions"]
        
        flags += additionals
        
        rel_rel_path_map = {}
        rel_abs_path_map = {}
        exes, _ = code_builds_factory.repository_manager.\
                                                    get_relative_exe_path_map()
        ERROR_HANDLER.assert_true(len(exes) == 1, \
                                "Only single exe supported in GCOV", __file__)
        for exe in exes:
            filename = os.path.basename(exe)
            rel_rel_path_map[exe] = filename
            rel_abs_path_map[exe] = os.path.join(\
                                self.instrumented_code_storage_dir, filename)

        self.instrument_callback_obj = self.InstrumentCallbackObject()
        self.instrument_callback_obj.set_post_callback_args(\
                                        (self.gc_files_dir, rel_abs_path_map))
        pre_ret, ret, post_ret = code_builds_factory.transform_src_into_dest(\
                        src_fmt=CodeFormats.C_SOURCE,\
                        dest_fmt=CodeFormats.NATIVE_CODE,\
                        src_dest_files_paths_map=None,\
                        compiler=prog, flags_list=flags, clean_tmp=True, \
                        reconfigure=True, \
                        callback_object=self.instrument_callback_obj)
        
        # Check
        if ret == common_mix.GlobalConstants.COMMAND_FAILURE:
            ERROR_HANDLER.error_exit("Program {} {}.".format(prog,\
                                        'built problematic'), __file__)

        # write down the rel_path_map
        ERROR_HANDLER.assert_true(not os.path.isfile(\
                self.instrumentation_details), "must not exist here", __file__)
        common_fs.dumpJSON(rel_rel_path_map, self.instrumentation_details)

    #~ def _do_instrument_code()
#~ class CriteriaToolGCov
