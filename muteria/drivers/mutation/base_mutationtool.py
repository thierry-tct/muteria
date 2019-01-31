
# This module is used through MetaMutationTool class
# Which access the relevant mutation tools as specified
# The tools are organized by programming language
# For each language, there is a folder for each tool, 
# named after the tool in lowercase

# Each mutation tool package have the following in the __init__.py file:
# import <Module>.<class extending BaseMutationTool> as MutationTool

from __future__ import print_function
import os, sys
import glob
import shutil

import muteria.common.matrices as common_matrices


class BaseMutationTool(object):
    '''
    '''

    def __init__(self, meta_test_generation_obj, mutation_working_dir, 
                                                    code_builder, config, checkpointer):
        self.meta_test_generation_obj = meta_test_generation_obj
        sefl.mutation_working_dir = mutation_working_dir
        self.code_builder = code_builder
        self.config = config
        self.checkpointer = checkpointer

        if self.mutation_working_dir is not None:
            if not os.path.isdir(self.mutation_working_dir):
                os.mkdir(self.mutation_working_dir)

        # Generate the mutants into this folder (to be created by user)
        self.mutants_storage_dir = os.path.join(
                        self.mutation_working_dir, "mutant_files")
        # TODO

    def get_checkpointer(self):
        return self.checkpointer

    def has_checkpointer(self):
        return self.checkpointer is not None

    @abc.abstractmethod
    def get_mutant_executable_path(self, mutant_id):
        print ("!!! Must be implemented in child class !!!")
    @abc.abstractmethod
    def get_mutant_environment_vars(self, mutant_id):
        '''
            return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def get_weakmutation_executable_path(self):
        print ("!!! Must be implemented in child class !!!")
    @abc.abstractmethod
    def get_weakmutation_environment_vars(self, result_dir_tmp):
        '''
            return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        test_result_file = os.path.join(result_dir_tmp, "test_weak_mutation")
        print ("!!! Must be implemented in child class !!!")
    @abc.abstractmethod
    def extract_weakmutation_data_of_a_test(self, result_dir_tmp):
        '''
            return: the list of mutants weakly killed as mutant id list
        '''
        test_result_file = os.path.join(result_dir_tmp, "test_weak_mutation")
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def get_mutantcoverage_executable_path(self):
        print ("!!! Must be implemented in child class !!!")
    @abc.abstractmethod
    def get_mutantcoverage_environment_vars(self, result_dir_tmp):
        '''
            return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        test_result_file = os.path.join(result_dir_tmp, "test_mutant_coverage")
        print ("!!! Must be implemented in child class !!!")
    @abc.abstractmethod
    def extract_mutantcoverage_data_of_a_test(self, result_dir_tmp):
        '''
            return: the list of covered mutants as mutant id list
        '''
        test_result_file = os.path.join(result_dir_tmp, "test_mutant_coverage")
        print ("!!! Must be implemented in child class !!!")

    def runtest_using_meta_mutant (self, testcases, result_matrix, mutantlist,
                                    get_executable_path_func,
                                    get_environment_vars_func,
                                    extract_data_of_a_test):
        '''
            param: testcases: list of testcase ids
        '''
        # Check that the result_matrix is empty and fine
        assert result_matrix.is_empty(), "the matrix must be empty"
        assert set(testcases) == 
                    set(result_matrix.get_nonkey_colname_list()),
            "The specified test cases are not same in the matrix"

        executable_path = self.get_executable_path_func()

        result_dir_tmp = os.path.join(self.mutation_working_dir, "mutant_meta_result_tmp")
        if os.isdir(result_dir_tmp):
            shutil.rmtree(result_dir_tmp)

        execution_environment_vars = self.get_environment_vars_func(
                                                                result_dir_tmp)

        update_data_dict = {mutant_id: {} for mutant_id in mutantlist}

        # Execute mutant coverage executable with test cases
        for testcase in testcases:
            # Create reult_tmp_dir
            os.mkdir(result_dir_tmp)

            # run testcase (expecting the coverage data output in env_vars) 
            verdict = self.meta_test_generation_obj.execute_testcase (testcase,
                                    exe_path=executable_path, 
                                    env_vars=execution_environment_vars)
            # extract covered mutants list
            covered_mutants = self.extract_data_of_a_test(result_dir_tmp)

            # Update the update_data_dict
            for mutant_id in set(update_data_dict) - set(covered_mutants):
                update_data_dict[mutant_id][testcase] = 
                                result_matrix.getInactiveCellVal()
            for mutant_id in covered_mutants:
                update_data_dict[mutant_id][testcase] = 
                                result_matrix.getActiveCellDefaultVal()
        
            # remove dir created for temporal storage
            shutil.rmtree(result_dir_tmp)

        # update the matrix form update_data_dict
        for key in update_data_dict:
            result_matrix.add_row_by_key(key, update_data_dict[key],
                                                                serialize=False)
        # Serialize to disk
        result_matrix.serialize()

    def runtest_mutant_coverage (self, testcases, mutant_coverage_matrix
                                    mutantlist):
        '''
            param: testcases: list of pairs of <testcase object> and <location>
        '''
        self.runtest_using_meta_mutant (testcases, mutant_coverage_matrix,
                                    mutantlist,
                                    self.get_mutantcoverage_executable_path,
                                    self.get_mutantcoverage_environment_vars,
                                    self.extract_mutantcoverage_data_of_a_test)

    def runtest_weak_mutation (self, testcases, weak_mutation_matrix,
                                     mutantlist):
        '''
        '''
        self.runtest_using_meta_mutant (testcases, weak_mutation_matrix,
                                    mutantlist,
                                    self.get_weakmutation_executable_path,
                                    self.get_weakmutation_environment_vars,
                                    self.extract_weakmutation_data_of_a_test)

    def runtest_strong_mutation (self, testcases, strong_mutation_matrix,
                                     mutantlist, serialize_period=1, 
                                     strong_kill_only_once=False):
        failverdict_to_val_map = {
                    True: strong_mutation_matrix.getActiveCellDefaultVal(),
                    False: strong_mutation_matrix.getInactiveCellVal()
                    meta_test_generation_obj.UNCERTAIN_TEST_VERDICT: \
                            strong_mutation_matrix.getUncertainCellDefaultVal()
        }

        assert serialize_period >= 1, "Serialize period must be an integer in [1,inf["

        for pos, mutant in enumerate(mutantlist):
            # execute mutant with the given testcases
            mutant_executable_path = get_mutant_executable_path(mutant)
            execution_environment_vars = \
                            self.get_mutant_environment_vars(mutant)
            fail_verdicts = self.meta_test_generation_obj.runtests(testcases,
                                    exe_path=mutant_executable_path, 
                                    env_vars=execution_environment_vars,
                                    stop_on_failure=strong_kill_only_once)
            
            # put in row format for matrix
            matrix_row_key = mutant
            matrix_row_values = {tc:failverdict_to_val_map[fail_verdicts[tc]] for tc in fail_verdicts}
            strong_mutation_matrix.add_row_by_key(matrix_row_key, matrix_row_values, serialize=(pos % serialize_period == 0))

        strong_mutation_matrix.serialize()

    def mutate_programs (self, outputdir=None, code_builder_override=None):
        '''
        '''
        if outputdir is None:
            outputdir = self.mutants_storage_dir
        if code_builder_override is None:
            code_builder_override = self.code_builder
        if os.path.isdir(outputdir):
            shutil.rmtree(outputdir)
        os.mkdir(outputdir)
        self.do_mutate_programs (outputdir=outputdir, 
                                    code_builder=code_builder_override)
        
    @abc.abstractmethod
    def do_mutate_programs (self, outputdir, code_builder):
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def prepare_original_code (self):
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def getMutantInfoObject(self):
        print ("!!! Must be implemented in child class !!!")

