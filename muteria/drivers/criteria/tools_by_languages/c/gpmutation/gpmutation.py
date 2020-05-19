
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

class CriteriaToolGPMutation(BaseCriteriaTool):
    def __init__(self, *args, **kwargs):
        BaseCriteriaTool.__init__(self, *args, **kwargs)
        self.instrumentation_details = os.path.join(\
                    self.instrumented_code_storage_dir, '.instru.meta.json')
        #self.wm_res_log_file = \
        #            "label_log."+TestCriteria.WEAK_MUTATION.get_field_value()
        #self.mcov_res_log_file = \
        #            "label_log."+TestCriteria.MUTANT_COVERAGE.get_field_value()
        self.mutant_data = os.path.join(self.instrumented_code_storage_dir,\
                                                            "mutant_data")
        self.gpmutation_out = os.path.join(self.mutant_data, 'gpmutation-out')
        self.separate_muts_folder_name = 'mutants.out'
        self.separate_muts_dir = os.path.join(self.gpmutation_out, \
                                                self.separate_muts_folder_name)
        self.archive_separated = True
    #~ def __init__()

    def _get_default_params(self):
        bool_params = {
            #'-keep-mutants-bc': None,
            #'-no-COV': None,
            #'-no-Meta': None,
            #'-no-WM': None, 
            #'-no-mutant-info': None,
            #'-print-preTCE-Meta': None,
            #'-write-mutants': None,
        }
        key_val_params = {
            #'-linking-flags': None,
            #'-mutant-config': None,
            #'-mutant-scope': None,
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
        for prog in ('gpmutation',):
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
                #TestCriteria.MUTANT_COVERAGE,
                #TestCriteria.WEAK_MUTATION,
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
        ERROR_HANDLER.error_exit(
                        "TODO: Not supported yet (single instrumented)",
                        __file__)

        '''crit_to_exes_map = {}
        obj = common_fs.loadJSON(self.instrumentation_details)
        #exes = [p for _, p in list(obj.items())]
        for c, c_exes in list(obj.items()):
            for k in c_exes:
                c_exes[k] = os.path.join(self.gpmutation_out, c_exes[k])

        for criterion in enabled_criteria:
            ERROR_HANDLER.assert_true(criterion.get_str() in obj, 
                            'criterion was not enabled during instrumentation'
                            ' with GPMutation: {}. Eneble it and run again'.format(\
                                                criterion.get_str()), __file__)
            crit_to_exes_map[criterion] = obj[criterion.get_str()]
        return crit_to_exes_map'''
    #~ def get_instrumented_executable_paths_map()

    def get_criterion_info_object(self, criterion):
        try:
            return self.mutant_info_object
        except AttributeError:
            minf_obj = MutantsInfoObject()

            gpmutation_inf_obj = common_fs.loadJSON(os.path.join(
                                    self.gpmutation_out, "mutantsInfo.json"))

            # Add elements
            for mid, info in list(gpmutation_inf_obj.items()):
                minf_obj.add_element(mid, mutant_type=info['Type'], \
                                        mutant_locs=info['SrcLoc'], \
                                        mutant_function_name=info['FuncName'])
            self.mutant_info_object = minf_obj
            return minf_obj
    #~ def get_criterion_info_object()

    def _get_single_exe_filename(self, criterion):
        ERROR_HANDLER.error_exit(
                        "TODO: Not supported yet (single instrumented)",
                        __file__)
        '''try:
            return self.single_exe_filename
        except AttributeError:
            inst_path_map = \
                        self.get_instrumented_executable_paths_map([criterion])
            tmp = inst_path_map[criterion]
            r_file = list(tmp.keys())[0]
            filename = os.path.splitext(os.path.basename(tmp[r_file]))[0]
            self.single_exe_filename = {r_file: filename}
            return self.single_exe_filename.copy()'''
    #~ def _get_single_exe_filename()

    def _get_criterion_element_executable_path(self, criterion, element_id):
#        self.sm_separate_exes = 
        ERROR_HANDLER.assert_true(self.get_criterion_info_object(criterion).\
                                            has_element(element_id),\
                        "Inexistant mutant id: "+element_id, __file__)
        
        rel_names = []
        mut_code = {}
        with open(self.instrumentation_details) as f:
            map_keys = f.readlines()
            ERROR_HANDLER.assert_true(len(map_keys) == 1, \
                            "only one executable supported for now", __file__)
            map_key = map_keys[0].strip()
        mut_code[map_key] = os.path.join(self.separate_muts_dir, element_id, \
                                                    os.path.basename(map_key)) 
        rel_names.append(os.path.join(self.separate_muts_folder_name, \
                                        element_id, os.path.basename(map_key)))
        # If archiving
        if self.archive_separated:
            archive_path = common_fs.TarGz.get_archive_filename_of(\
                                                        self.separate_muts_dir)
            ERROR_HANDLER.assert_true(os.path.isfile(archive_path), \
                                    "Archived separated mutant file missing",\
                                    __file__)
            if os.path.isdir(self.separate_muts_dir):
                shutil.rmtree(self.separate_muts_dir)
            # Extract the selected
            for arch_name in rel_names:
                err_msg = common_fs.TarGz.extractFromArchive(archive_path, \
                                                                    arch_name)
                ERROR_HANDLER.assert_true(err_msg is None, \
                            "failed to extract, err: "+str(err_msg), __file__)
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
                ERROR_HANDLER.error_exit(
                        "TODO: Not supported yet (single instrumented)",
                        __file__)
            elif c == TestCriteria.MUTANT_COVERAGE:
                ERROR_HANDLER.error_exit(
                        "TODO: Not supported yet (single instrumented)",
                        __file__)
            else:
                res[c] = None
        return res
    #~ def _get_criteria_environment_vars()

    def _collect_temporary_coverage_data(self, criteria_name_list, \
                                            test_execution_verdict, \
                                            used_environment_vars, \
                                            result_dir_tmp, \
                                            testcase):
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

        ERROR_HANDLER.error_exit(
                        "TODO: Not supported yet (single instrumented)",
                        __file__)
        '''
        def extract_covered(filename, criterion):
            mutant_id_set = set(self.get_criterion_info_object(criterion).\
                                                        get_elements_list())
            cov_res = {
                    m: common_mix.GlobalConstants.ELEMENT_NOTCOVERED_VERDICT\
                                                    for m in mutant_id_set}
            if os.path.isfile(filename):
                with open(filename) as f:
                    for line in f:
                        mut_id = line.strip()
                        # use if because gpmutation currently do not update 
                        # WM and MCOV after fdupes TCE
                        if mut_id in mutant_id_set: 
                            cov_res[mut_id] = common_mix.GlobalConstants\
                                                    .ELEMENT_COVERED_VERDICT
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
        '''
    #~ def _extract_coverage_data_of_a_test()

    def _do_instrument_code (self, exe_path_map, \
                                        code_builds_factory, \
                                        enabled_criteria, parallel_count=1):
        # Setup
        if os.path.isdir(self.instrumented_code_storage_dir):
            shutil.rmtree(self.instrumented_code_storage_dir)
        os.mkdir(self.instrumented_code_storage_dir)
        if os.path.isdir(self.mutant_data):
            shutil.rmtree(self.mutant_data)
        os.mkdir(self.mutant_data)

        prog = 'gpmutation'
        if self.custom_binary_dir is not None:
            prog = os.path.join(self.custom_binary_dir, prog)
            ERROR_HANDLER.assert_true(os.path.isfile(prog), \
                            "The tool {} is missing from the specified dir {}"\
                                        .format(os.path.basename(prog), \
                                            self.custom_binary_dir), __file__)

        exes, _ = code_builds_factory.repository_manager.\
                                                    get_relative_exe_path_map()

        ERROR_HANDLER.assert_true(len(exes) == 1, \
                                        "Support only a singe exe", __file__)

        gpmutation_subj = os.path.basename(exes[0])
        args=[gpmutation_subj, self.separate_muts_dir]

        # Execute GPMutation
        ret, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                                        prog, args_list=args)
        if (ret != 0):
            logging.error(out)
            logging.error(err)
            logging.error("\n>> CMD: " + " ".join([prog]+args) + '\n')
            ERROR_HANDLER.error_exit("gpmutation failed!", __file__)
        
        # write down the rel_path_map
        ERROR_HANDLER.assert_true(not os.path.isfile(\
                self.instrumentation_details), "must not exist here", __file__)
        
        with open (self.instrumentation_details, 'w') as f:
            for exe in exes:
                f.write(exe+'\n')

        # Archive separated if on
        if self.archive_separated:
            err_msg = common_fs.TarGz.compressDir(self.separate_muts_dir, \
                                                    remove_in_directory=True)
            ERROR_HANDLER.assert_true(err_msg is None,\
                                "Compression failed: "+str(err_msg), __file__)
    #~ def _do_instrument_code()

    ## Extra functions for gpmutation
    def get_test_gen_metamutant_bc(self):
        ERROR_HANDLER.error_exit(
                        "TODO: Not supported yet (single instrumented)",
                        __file__)
        '''
        ERROR_HANDLER.assert_true(os.path.isfile(self.instrumentation_details), \
		 "Are you sure mutant generation with GPMutation was ran?"
                 "This is needed before meta mu bc is called", __file__)
        crit2file = self.get_instrumented_executable_paths_map(\
                                            (TestCriteria.STRONG_MUTATION,))
        sm_map = list(crit2file[TestCriteria.STRONG_MUTATION].items())
        ERROR_HANDLER.assert_true(len(sm_map) == 1, \
                                "Expects exactly 1 file for Strong Mutation")
        exe_name, filepath = sm_map[0]
        return filepath + '.bc'
        '''
    #~ def get_test_gen_metamutant_bc()
#~ class CriteriaToolGPMutation
