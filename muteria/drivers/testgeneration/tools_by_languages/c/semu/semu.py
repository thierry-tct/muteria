
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

from muteria.drivers.testgeneration.tools_by_languages.c.semu.driver_config \
                                        import DriverConfigSemu, MetaMuSource

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
        
        self.driver_config = None
        if self.config.get_tool_user_custom() is not None:
            self.driver_config = \
                            self.config.get_tool_user_custom().DRIVER_CONFIG
        if self.driver_config is None:
            self.driver_config = DriverConfigSemu()
        else:
            ERROR_HANDLER.assert_true(isinstance(self.driver_config, \
                                            DriverConfigSemu),\
                                            "invalid driver config", __file__)

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
          
            '-only-replay-seeds': None, # Useful to set this is using seeds
            # SEMu 
            '-semu-no-state-difference': None,
            '-semu-MDO-propagation-selection-strategy': None,
            '-semu-use-basicblock-for-distance': None,
            '-semu-forkprocessfor-segv-externalcalls': True,
            '-semu-testsgen-only-for-critical-diffs': None,
            '-semu-no-environment-output-diff': None,
            '-semu-use-only-multi-branching-for-depth': None,
            '-semu-disable-post-mutation-check': None,
            '-semu-no-error-on-memory-limit': None,
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
          
            '-'+self.SEED_DIR_ARG_NAME: None, 
            # SEMu 
            '-semu-checkpoint-window': '0', #None,
            '-semu-minimum-propagation-depth': '2', # None,
            '-semu-propagation-proportion': '0.25', #None,
            '-semu-precondition-length': '0', #None,
            '-semu-max-total-tests-gen': None,
            '-semu-number-of-tests-per-mutant': '5', # None,
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
    
    def _handle_backward_compatibility_with_semu (self, args):
        to_replace_map = {
            '-semu-mutant-max-fork': '-semu-checkpoint-window',
            '--semu-mutant-max-fork': '--semu-checkpoint-window',
            '-semu-mutant-state-continue-proba': \
                                            '-semu-propagation-proportion',
            '--semu-mutant-state-continue-proba': \
                                           '--semu-propagation-proportion',
            '-semu-continue-mindist-out-heuristic': \
                                '-semu-MDO-propagation-selection-strategy',
            '--semu-continue-mindist-out-heuristic': \
                                '--semu-MDO-propagation-selection-strategy',
            '-semu-checknum-before-testgen-for-discarded': \
                                        '-semu-minimum-propagation-depth',
            '--semu-checknum-before-testgen-for-discarded': \
                                        '--semu-minimum-propagation-depth',
            '-semu-disable-statediff-in-testgen': \
                                               '-semu-no-state-difference',
            '--semu-disable-statediff-in-testgen': \
                                            '--semu-no-state-difference',
            '-semu-max-tests-gen-per-mutant': \
                                        '-semu-number-of-tests-per-mutant',
            '--semu-max-tests-gen-per-mutant': \
                                        '--semu-number-of-tests-per-mutant'
        }
        
        # Direct replace
        for pos, val in enumerate(args):
            for match, replace in to_replace_map.items():
                if val == match:
                    args[pos] = replace
                    break
                    
        # negation (Now out env is set by default)
        found_pos = None
        for match in ['-semu-consider-outenv-for-diffs', \
                                    '--semu-consider-outenv-for-diffs']:
            try:
                pos = args.index(match)
                # present
                ERROR_HANDLER.assert_true (found_pos is None, \
                                 "Multiple occurence of "
                           "'-semu-consider-outenv-for-diffs'", __file__)
                found_pos = pos
            except ValueError:
                # abscent
                pass
        if found_pos is None:
            # insert no outenv
            args.insert(0, '--semu-no-environment-output-diff')
        else:
            del args[found_pos]
    #~ def _handle_backward_compatibility_with_semu()
    
    def _call_generation_run(self, runtool, args):
        # Handle support for alod version of SEMu
        self._handle_backward_compatibility_with_semu (args)
        
        # If seed-dir is set, ensure that only-replay-seeds is set 
        # (semu requires it for now)
        seed_dir_key = self.SEED_DIR_ARG_NAME
        only_replay_seeds_flag = '-only-replay-seeds'
        if self.get_value_in_arglist(args, seed_dir_key) is not None:
            if only_replay_seeds_flag not in args and \
                                  '-'+only_replay_seeds_flag not in args: 
                logging.warning("SEMu requires '-only-replay-seeds' flag to"
                                " be set when using seeds. Muteria set it"
                                " autmatically")
                args.insert(0, only_replay_seeds_flag)
                
        # use mutants_by_funcs to reorganize target mutants for scalability

        max_mutant_count_per_cluster = \
                        self.driver_config.get_max_mutant_count_per_cluster()

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
    
    def _get_compile_flags_list(self):
        return ['-DMUTERIA_FOR_SEMU_TEST_GENERATION']
    #~ def _get_compile_flags_list()

    def _get_input_bitcode_file(self, code_builds_factory, rel_path_map, \
                                                meta_criteria_tool_obj=None):
        meta_mu_src = self.driver_config.get_meta_mutant_source()

        # XXX Case of manual annotation
        if meta_mu_src == MetaMuSource.ANNOTATION:
            with open(self.cand_muts_file, 'w') as f:
                # Single mutant (id 1, corresponding to old version)
                f.write(str(1)+'\n')
            return super(TestcasesToolSemu, self)._get_input_bitcode_file(\
                                        code_builds_factory, rel_path_map, \
                                meta_criteria_tool_obj=meta_criteria_tool_obj)
        
        # XXX: Case of other mutation tools like Mart
        # get the meta criterion file from MART or any compatible tool.
        mutant_gen_tool_name = meta_mu_src.get_field_value()
        mut_tool_alias_to_obj = \
                            meta_criteria_tool_obj.get_criteria_tools_by_name(\
                                                        mutant_gen_tool_name)

        if len(mut_tool_alias_to_obj) == 0:
            logging.warning(\
                'SEMu requires {} to generate mutants but none used'.format(\
                                                        mutant_gen_tool_name))

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

        cand_muts = list(single_tool_obj.get_elements_list())
        
        for mut in single_tool_obj.get_elements_list():
            func = single_tool_obj.get_element_data(mut)[\
                                                        'mutant_function_name']
            #meta_mut = DriversUtils.make_meta_element(mut, single_alias)
            if func not in self.mutants_by_funcs:
                self.mutants_by_funcs[func] = set()
            self.mutants_by_funcs[func].add(mut) #meta_mut)

        # XXX: get candidate mutants list
        if self.driver_config.get_target_only_live_mutants() \
                                        and os.path.isfile(self.sm_mat_file):
            sm_mat = common_matrices.ExecutionMatrix(\
                                                filename=self.sm_mat_file)
            mut2killing_tests = sm_mat.query_active_columns_of_rows()
            alive_muts = [m for m, k_t in mut2killing_tests.items() \
                                                        if len(k_t) == 0]
            cand_muts = []
            for meta_m in alive_muts:
                t_alias, m = DriversUtils.reverse_meta_element(meta_m)
                if t_alias in t_alias2metamu_bc: # There is a single one
                    cand_muts.append(m)

        with open(self.cand_muts_file, 'w') as f:
            for m in cand_muts:
                f.write(str(m)+'\n')

        return t_alias2metamu_bc[list(t_alias2metamu_bc)[0]]
    #~ def _get_input_bitcode_file()

    @staticmethod
    def _get_generation_time_of_test(test, test_top_dir):
        """ extract the generation timestamp of a test. the test and 
            its top location are specified
        """
        test_path = os.path.join(test_top_dir, test)
        # Seach the test and get the time. 
        # If dup, get the time of the duplicate test
        # 1. If test_path exist, is is not dup
        to_search = None
        if os.path.isfile(test_path):
            to_search = test_path
        else:
            # seach the test it is dup of
            kepttest2duptest_map = common_fs.loadJSON(\
                                              self.keptktest2dupktests)
            ERROR_HANDLER.asser_true(test not in kepttest2duptest_map, \
                            "Test file not existing but in kept (BUG)", \
                                                                __file__)
            for kept, dup_list in kepttest2duptest_map.items():
                if test in dup_list:
                    to_search = os.path.join(test_top_dir, kept)
        
        ERROR_HANDLER.assert_true(to_search is not None, \
                        "test not found in dup and inexistant", __file__)
        # 2. search for the test and its time
        ktestlists = glob.glob(os.path.join(os.path.dirname(to_search), \
                                              "mutant-[0-9]*.ktestlist"))
        gen_time = None
        for klist in ktestlists:
            df = common_fs.loadCSV(klist,  separator=",")
            val = df.loc[df.ktest==os.path.basename(to_search), \
                                                'ellapsedTime(s)'].values
            if len(val) == 1:
                gen_time = val[0]
                break
            ERROR_HANDLER.assert_true(len(val) == 0, "PB in ktestlist " + \
                  str(klist) + ". ktest appearing multiple times", __file__)
        ERROR_HANDLER.assert_true(gen_time is not None, \
                                   "test not found in ktestlists", __file__)
        return gen_time
    #~ def _get_generation_time_of_test()
    
    def fdupeGeneratedTest (self, mfi_ktests_dir_top, mfi_ktests_dir, \
                                                semuoutputs, seeds_dir=None):
        # Implement and use (see run.py in Semu Analysis)
        # TODO, implement this
        ERROR_HANDLER.error_exit("TODO: implement fdupesGeneratedTest")
    #~ def fdupeGeneratedTest ()

    def requires_criteria_instrumented(self):
        return True
    #~ def requires_criteria_instrumented()
#~ class TestcasesToolSemu
