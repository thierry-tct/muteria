
from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import resource
import random

import numpy as np

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix
import muteria.common.matrices as common_matrices

import muteria.drivers.criteria as criteria
import muteria.controller.explorer as fd_structure

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.drivers.testgeneration.base_testcasetool import BaseTestcaseTool
from muteria.drivers.testgeneration.testcases_info import TestcasesInfoObject
from muteria.drivers import DriversUtils
from muteria.drivers.testgeneration.testcase_formats.ktest.ktest \
                                                        import KTestTestFormat
from muteria.drivers.testgeneration.tools_by_languages.c.klee.klee \
                                                    import TestcasesToolKlee

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesToolSemu(TestcasesToolKlee):

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        for prog in ('klee-semu',):
            if custom_binary_dir is not None:
                prog = os.path.join(custom_binary_dir, prog)
            if not DriversUtils.check_tool(prog=prog, args_list=['--version'],\
                                                    expected_exit_codes=[0,1]):
                return False

        return KTestTestFormat.installed(custom_binary_dir=custom_binary_dir)
    #~ def installed()

    def __init__(self, *args, **kwargs):
        TestcasesToolKlee.__init__(self, *args, **kwargs)
        self.cand_muts_file = os.path.join(self.tests_working_dir, \
                                                        "cand_muts_file.txt")
        self.sm_mat_file = self.head_explorer.get_file_pathname(\
                            fd_structure.CRITERIA_MATRIX[criteria.TestCriteria\
                                                            .STRONG_MUTATION])
        self.mutants_by_funcs = None
    #~ def __init__()

    # SHADOW override
    def _get_default_params(self):
        bool_params = {
            '-ignore-solver-failures': None,
            '-allow-external-sym-calls': True, #None,
            '-posix-runtime': True, #None,
            '-dump-states-on-halt': True, #None,
            '-only-output-states-covering-new': None,
            '-use-cex-cache': True,
            # SEMu 
            '-semu-disable-statediff-in-testgen': None,
            '-semu-continue-mindist-out-heuristic': None,
            '-semu-use-basicblock-for-distance': None,
            '-semu-forkprocessfor-segv-externalcalls': True,
            '-semu-testsgen-only-for-critical-diffs': None,
            '-semu-consider-outenv-for-diffs': None,
        }
        key_val_params = {
            '-output-dir': self.tests_storage_dir,
            '-solver-backend': 'z3',
            '-max-solver-time': '300',
            '-search': 'bfs',
            '-max-memory': None,
            '-max-time': self.config.TEST_GENERATION_MAXTIME,
            '-libc': 'uclibc',
            '-max-sym-array-size': '4096',
            '-max-instruction-time': '10.',
            # SEMu 
            '-semu-mutant-max-fork': '0', #None,
            '-semu-checknum-before-testgen-for-discarded': '2', # None,
            '-semu-mutant-state-continue-proba': '0.25', #None,
            '-semu-precondition-length': '0', #None,
            '-semu-max-total-tests-gen': None,
            '-semu-max-tests-gen-per-mutant': '5', # None,
            '-semu-loop-break-delay': '120.0',
        }
        key_val_params.update({
                                })
        # XXX: set muts cand list
        if os.path.isfile(self.sm_mat_file):
            key_val_params['-semu-candidate-mutants-list-file'] = \
                                                        self.cand_muts_file
        return bool_params, key_val_params
    #~ def _get_default_params()
    
    def _call_generation_run(self, runtool, args):
        # use mutants_by_funcs to reorganize target mutants for scalability

        max_mutant_count_per_cluster = self.get_value_in_arglist(args, \
                                        'DRIVER_max_mutant_count_per_cluster')
        if max_mutant_count_per_cluster is None:
            # TODO: compute max_mutant_count_per_cluster based on max memory
            max_mutant_count_per_cluster = 100
        else:
            max_mutant_count_per_cluster = float(max_mutant_count_per_cluster)
            self.remove_arg_and_value_from_arglist(args, \
                                        'DRIVER_max_mutant_count_per_cluster')

        cand_mut_file_bak = self.cand_muts_file + '.bak'
        mut_list = []
        with open(self.cand_muts_file) as f:
            for m in f:
                m = m.strip()
                ERROR_HANDLER.assert_true(m.isdigit(), "Invalid mutant ID", \
                                                                    __file__)
                mut_list.append(m)
        if self.mutants_by_funcs is None:
            random.shuffle(mut_list)
        else:
            # make the mutants to be localized in same function as much as
            # possible
            # XXX Here the mutant ID are NOT meta but simple IDs
            this_mutants_by_funcs = {}
            mut_to_func = {}
            for f, m_set in self.mutants_by_funcs.items():
                this_mutants_by_funcs[f] = m_set & set(mut_list)
                for m in this_mutants_by_funcs[f]:
                    mut_to_func[m] = f
            func_to_rank_dec = list(this_mutants_by_funcs.keys())
            func_to_rank_dec.sort(key=lambda x: len(this_mutants_by_funcs[x]),\
                                                                reverse=True)
            func_to_rank_dec = {f: r for r, f in enumerate(func_to_rank_dec)}
            mut_list.sort(key=lambda x: func_to_rank_dec[mut_to_func[x]])
        nclust = int(len(mut_list) / max_mutant_count_per_cluster)
        if len(mut_list) != max_mutant_count_per_cluster * nclust:
            nclust += 1
        clusters = np.array_split(mut_list, nclust)

        # update max-time
        if len(clusters) > 1:
            cur_max_time = float(self.get_value_in_arglist(args, 'max-time'))
            self.set_value_in_arglist(args, 'max-time', \
                                    str(max(1, cur_max_time / len(clusters))))
        
        shutil.move(self.cand_muts_file, cand_mut_file_bak)

        c_dirs = []
        for c_id, clust in enumerate(clusters):
            logging.debug("SEMU: targeting mutant cluster {}/{} ...".format(\
                                                        c_id+1, len(clusters)))
            with open(self.cand_muts_file, 'w') as f:
                for m in clust:
                    f.write(m+'\n')

            super(TestcasesToolSemu, self)._call_generation_run(runtool, args)
            
            c_dir = os.path.join(os.path.dirname(self.tests_storage_dir), \
                                                                    str(c_id))
            shutil.move(self.tests_storage_dir, c_dir)
            c_dirs.append(c_dir)

        os.mkdir(self.tests_storage_dir)
        for c_dir in c_dirs:
            shutil.move(c_dir, self.tests_storage_dir)

        shutil.move(cand_mut_file_bak, self.cand_muts_file)
    #~ def _call_generation_run()

    def _get_tool_name(self):
        return 'klee-semu'
    #~ def _get_tool_name()
    
    def _get_input_bitcode_file(self, code_builds_factory, rel_path_map, \
                                                meta_criteria_tool_obj=None):
        # XXX: get the meta criterion file from MART.
        mutant_gen_tool_name = 'mart'
        mut_tool_alias_to_obj = \
                            meta_criteria_tool_obj.get_criteria_tools_by_name(\
                                                        mutant_gen_tool_name)

        if len(mut_tool_alias_to_obj) == 0:
            logging.warning(\
                        'SEMu requires Mart to generate mutants but none used')

        ERROR_HANDLER.assert_true(len(mut_tool_alias_to_obj) == 1, \
                                "SEMu supports tests generation from"
                                "a single .bc file for now (todo).", __file__)

        t_alias2metamu_bc = {}
        t_alias2mutantInfos = {}
        for alias, obj in mut_tool_alias_to_obj.items():
            dest_bc = rel_path_map[list(rel_path_map)[0]]+'.bc'
            shutil.copy2(obj.get_test_gen_metamutant_bc(), dest_bc)
            t_alias2metamu_bc[alias] = dest_bc
            t_alias2mutantInfos[alias] = obj.get_criterion_info_object(None)

        # XXX: get mutants ids by functions
        self.mutants_by_funcs = {}
        single_alias = list(t_alias2mutantInfos)[0]
        single_tool_obj = t_alias2mutantInfos[single_alias]
        for mut in single_tool_obj.get_elements_list():
            func = single_tool_obj.get_element_data(mut)[\
                                                        'mutant_function_name']
            #meta_mut = DriversUtils.make_meta_element(mut, single_alias)
            if func not in self.mutants_by_funcs:
                self.mutants_by_funcs[func] = set()
            self.mutants_by_funcs[func].add(mut) #meta_mut)

        # XXX: get candidate mutants list
        if os.path.isfile(self.sm_mat_file):
            sm_mat = common_matrices.ExecutionMatrix(filename=self.sm_mat_file)
            mut2killing_tests = sm_mat.query_active_columns_of_rows()
            alive_muts = [m for m, k_t in mut2killing_tests.items() \
                                                            if len(k_t) == 0]
            with open(self.cand_muts_file, 'w') as f:
                for meta_m in alive_muts:
                    t_alias, m = DriversUtils.reverse_meta_element(meta_m)
                    if t_alias in t_alias2metamu_bc: # There is a single one
                        f.write(str(m)+'\n')

        return t_alias2metamu_bc[list(t_alias2metamu_bc)[0]]
    #~ def _get_input_bitcode_file()

    def requires_criteria_instrumented(self):
        return True
    #~ def requires_criteria_instrumented()
#~ class TestcasesToolSemu