
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
from muteria.drivers.criteria.criteria_info import MutantsInfoObject

ERROR_HANDLER = common_mix.ErrorHandler

class CriteriaToolMart(BaseCriteriaTool):
    def __init__(self, *args, **kwargs):
        BaseCriteriaTool.__init__(self, *args, **kwargs)
        self.instrumentation_details = os.path.join(\
                    self.instrumented_code_storage_dir, '.instru.meta.json')
        self.wm_res_log_file = \
                    "label_log."+TestCriteria.WEAK_MUTATION.get_field_value()
        self.mcov_res_log_file = \
                    "label_log."+TestCriteria.MUTANT_COVERAGE.get_field_value()
        self.mutant_data = os.path.join(self.instrumented_code_storage_dir,\
                                                            "mutant_data")
        self.mart_out = os.path.join(self.mutant_data, 'mart-out-0')
        self.separate_muts_dir = os.path.join(self.mart_out, 'mutants.out')
    #~ def __init__()

    def _get_default_params(self):
        bool_params = {
            '-keep-mutants-bc': None,
            '-no-COV': None,
            '-no-Meta': None,
            '-no-WM': None, 
            '-no-mutant-info': None,
            '-print-preTCE-Meta': None,
            '-write-mutants': None,
        }
        key_val_params = {
            '-linking-flags': None,
            '-mutant-config': None,
            '-mutant-scope': None,
        }
        return bool_params, key_val_params
    #~ def _get_default_params()

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        for prog in ('mart'):
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
                TestCriteria.MUTANT_COVERAGE,
                TestCriteria.WEAK_MUTATION,
               ]
    #~ def _get_meta_instrumentation_criteria()

    @classmethod
    def _get_separated_instrumentation_criteria(cls):
        """ Criteria where all elements are instrumented in different files
            :return: list of citeria
        """
        return [TestCriteria.STRONG_MUTATION]
    #~ def _get_separated_instrumentation_criteria()

    def get_instrumented_executable_paths_map(self, enabled_criteria):
        crit_to_exes_map = {}
        obj = common_fs.loadJSON(self.instrumentation_details)
        #exes = [p for _, p in list(obj.items())]
        for c, c_exes in list(obj.items()):
            for k in c_exes:
                c_exes[k] = os.path.join(self.mart_out, c_exes[k])

        for criterion in enabled_criteria:
            crit_to_exes_map[criterion] = obj[criterion.get_str()]
        return crit_to_exes_map
    #~ def get_instrumented_executable_paths_map()

    def get_criterion_info_object(self, criterion):
        try:
            return self.mutant_info_object
        except AttributeError:
            minf_obj = MutantsInfoObject()
            mart_inf = os.path.join(self.mart_out, 'mutantsInfos.json')
            fdupes = os.path.join(self.mart_out, 'fdupes_duplicates.json')
            #in_mem_tce = os.path.join(self.mart_out, 'equidup-mutantsInfos.json')

            mart_inf_obj = common_fs.loadJSON(mart_inf)
            fduped_obj = common_fs.loadJSON(fdupes)
            #in_mem_tce_obj = common_fs.loadJSON(in_mem_tce)

            # remove equivalent et duplicates
            for mid, dups in list(fduped_obj.items()):
                for d_mid in dups:
                    del mart_inf_obj[d_mid]

            # Add elements
            for mid, info in list(mart_inf_obj.items()):
                minf_obj.add_element(mid, mutant_type=info['Type'], \
                                            mutant_locs=info['SrcLoc'], \
                                            mutant_function=info['FuncName'], \
                                            IRPosInFunc=info['IRPosInFunc'])
            self.mutant_info_object = minf_obj
            return minf_obj
    #~ def get_criterion_info_object(self, criterion)

    def _get_single_exe_filename(self, criterion):
        try:
            return self.single_exe_filename
        except AttributeError:
            inst_path_map = \
                        self.get_instrumented_executable_paths_map([criterion])
            tmp = inst_path_map[criterion]
            r_file = list(tmp.keys())[0]
            filename = os.path.splitext(os.path.basename(tmp[r_file]))[0]
            self.single_exe_filename = {r_file: filename}
            return self.single_exe_filename.copy()
    #~ def _get_single_exe_filename()

    def _get_criterion_element_executable_path(self, criterion, element_id):
#        self.sm_separate_exes = 
        ERROR_HANDLER.assert_true(self.get_criterion_info_object(criterion).\
                                            has_element(element_id),\
                        "Inexistant mutant id: "+element_id, __file__)
        
        mut_code = {k:os.path.join(self.separate_muts_dir, element_id, v) for \
                    k,v in self._get_single_exe_filename(criterion).items()}
        return mut_code
    #~ def _get_criterion_element_executable_path()

    def _get_criterion_element_environment_vars(self, criterion, element_id):
        '''
            return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        return None
    #~ def _get_criterion_element_environment_vars()

    def _get_criteria_environment_vars(self, result_dir_tmp, enabled_criteria):
        '''
        return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        res = {}
        for c in enabled_criteria:
            if c == TestCriteria.WEAK_MUTATION:
                res[c] = {'MART_WM_LOG_OUTPUT': os.path.join(result_dir_tmp, \
                                                        self.wm_res_log_file)}
            elif c == TestCriteria.MUTANT_COVERAGE:
                res[c] = {'MART_WM_LOG_OUTPUT': os.path.join(result_dir_tmp, \
                                                    self.mcov_res_log_file)}
            else:
                res[c] = None
        return res
    #~ def _get_criteria_environment_vars()

    def _collect_temporary_coverage_data(self, criteria_name_list, \
                                            test_execution_verdict, \
                                            used_environment_vars, \
                                                    result_dir_tmp):
        ''' Get the list of mutants id weakly killed or covered
        '''
        pass
    #~ def _collect_temporary_coverage_data()

    def _extract_coverage_data_of_a_test(self, enabled_criteria, \
                                    test_execution_verdict, result_dir_tmp):
        ''' read json files and extract data
            return: the dict of criteria with covering count
        '''
        ERROR_HANDLER.assert_true(TestCriteria.STRONG_MUTATION not in \
                                                        enabled_criteria, \
                            "SM metamutant run not yet supported", __file__)

        def extract_covered(filename, criterion):
            mutant_id_list = self.get_criterion_info_object(criterion).\
                                                            get_elements_list()
            cov_res = {
                    m: common_mix.GlobalConstants.ELEMENT_NOTCOVERED_VERDICT\
                                                    for m in mutant_id_list}
            with open(filename) as f:
                for line in f:
                    mut_id = line.strip()
                    cov_res[mut_id] = \
                            common_mix.GlobalConstants.ELEMENT_COVERED_VERDICT
            return cov_res
        #~ def extract_covered()

        res = {}
        if TestCriteria.WEAK_MUTATION in enabled_criteria:
            res[TestCriteria.WEAK_MUTATION] = extract_covered(\
                        os.path.join(result_dir_tmp, self.wm_res_log_file), \
                                                    TestCriteria.WEAK_MUTATION)
        if TestCriteria.MUTANT_COVERAGE in enabled_criteria:
            res[TestCriteria.MUTANT_COVERAGE] = extract_covered(\
                        os.path.join(result_dir_tmp, self.mcov_res_log_file), \
                                                TestCriteria.MUTANT_COVERAGE)

        return res
    #~ def _extract_coverage_data_of_a_test()

    def _do_instrument_code (self, outputdir, exe_path_map, \
                                        code_builds_factory, \
                                        enabled_criteria, parallel_count=1):
        # Setup
        if os.path.isdir(self.instrumented_code_storage_dir):
            shutil.rmtree(self.instrumented_code_storage_dir)
        os.mkdir(self.instrumented_code_storage_dir)
        if os.path.isdir(self.mutant_data):
            shutil.rmtree(self.mutant_data)
        os.mkdir(self.mutant_data)

        prog = 'mart'

        # get llvm compiler path
        ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                                        prog, ['--version'])
        llvm_compiler_path = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('LLVM tools dir:'):
                llvm_compiler_path = line.split()[3]#[1:-1]
                break
        
        ERROR_HANDLER.assert_true(llvm_compiler_path is not None, \
                                'Problem getting llvm path for mart', __file__)

        # Build into LLVM
        back_llvm_compiler = 'clang'
        rel_path_map = {}
        exes, _ = code_builds_factory.repository_manager.\
                                                    get_relative_exe_path_map()
        for exe in exes:
            filename = os.path.basename(exe)
            rel_path_map[exe] = os.path.join(self.mutant_data, filename)
        pre_ret, ret, post_ret = code_builds_factory.transform_src_into_dest(\
                        src_fmt=CodeFormats.C_SOURCE,\
                        dest_fmt=CodeFormats.LLVM_BITCODE,\
                        src_dest_files_paths_map=rel_path_map,\
                        compiler=back_llvm_compiler, flags_list=['-g'], \
                        clean_tmp=True, reconfigure=True, \
                        llvm_compiler_path=llvm_compiler_path)
        if ret == common_mix.GlobalConstants.TEST_EXECUTION_ERROR:
            ERROR_HANDLER.error_exit("Program {}.".format(\
                                'LLVM (clang) built problematic'), __file__)

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

        # mart params
        bool_param, k_v_params = self._get_default_params()
        if TestCriteria.STRONG_MUTATION in enabled_criteria:
            bool_param['-write-mutants'] = True

        args = [bp for bp, en in list(bool_param.items()) if en]
        for k,v in list(k_v_params.items()):
            if v is not None:
                args += [k,v]
        args.append(bitcode_file)
        
        # Execute Mart
        cwd = os.getcwd()
        os.chdir(self.mutant_data)
        ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                                                    prog, args)
        os.chdir(cwd)

        if (ret != 0):
            logging.error(out)
            logging.error(err)
            logging.error("\n>> CMD: " + " ".join([prog]+args))
            ERROR_HANDLER.error_exit("\nmart failed'", __file__)
        
        # write down the rel_path_map
        ERROR_HANDLER.assert_true(not os.path.isfile(\
                self.instrumentation_details), "must not exist here", __file__)
        store_obj = {c.get_str(): {} for c in enabled_criteria}
        for k,v in list(rel_path_map.items()):
            exe_file = os.path.basename(v)
            if TestCriteria.WEAK_MUTATION in enabled_criteria:
                crit_str = TestCriteria.WEAK_MUTATION.get_str()
                store_obj[crit_str][k] = exe_file+'.WM'
            if TestCriteria.MUTANT_COVERAGE in enabled_criteria:
                crit_str = TestCriteria.MUTANT_COVERAGE.get_str()
                store_obj[crit_str][k] = exe_file+'.COV'
            if TestCriteria.STRONG_MUTATION in enabled_criteria:
                crit_str = TestCriteria.STRONG_MUTATION.get_str()
                store_obj[crit_str][k] = exe_file+'.MetaMu'
        common_fs.dumpJSON(store_obj, self.instrumentation_details)

    #~ def _do_instrument_code()
#~ class CriteriaToolMart
