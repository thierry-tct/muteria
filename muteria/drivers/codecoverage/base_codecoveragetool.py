
# The tools are organized by programming language
# For each language, there is a folder for each tool, 
# named after the tool in lowercase

# Each codecoverage tool package have the following in the __init__.py file:
# import <Module>.<class extending BaseCodecoverageTool> as CodecoverageTool

from __future__ import print_function
import os, sys
import glob
import shutil

import muteria.common.matrices as common_matrices


class BaseCodecoverageTool(object):
    '''
    '''

    # Do not modify these constants in chidren classes
    STATEMENT_KEY = "STATEMENT_COVERAGE"
    BRANCH_KEY = "BRANCH_COVERAGE"
    FUNCTION_KEY = "FUNCTION_COVERAGE"

    def __init__(self, meta_test_generation_obj, codecoverage_working_dir, 
                                                    code_builder, config):
        self.meta_test_generation_obj = meta_test_generation_obj
        sefl.codecoverage_working_dir = codecoverage_working_dir
        self.code_builder = code_builder
        self.config = config

        if self.codecoverage_working_dir is not None:
            if not os.path.isdir(self.codecoverage_working_dir):
                os.mkdir(self.codecoverage_working_dir)

        # put the instrumented code into this folder (to be created by user)
        self.instrumented_code_storage_dir = os.path.join(
                        self.codecoverage_working_dir, "instrumented_code")

    def get_checkpointer(self):
        return self.checkpointer

    def has_checkpointer(self):
        return self.checkpointer is not None

    @abc.abstractmethod
    def getSupportedCriteria():
        #return [STATEMENT_KEY, BRANCH_KEY, FUNCTION_KEY]
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def get_instrumented_executable_paths(self, criterion_to_enabling):
        print ("!!! Must be implemented in child class !!!")
    @abc.abstractmethod
    def get_codecoverage_environment_vars(self, result_dir_tmp, \
                                                    criterion_to_enabling):
        '''
        return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def self.collect_temporary_coverage_data(criteria_name_list, \
                                            used_environment_vars, \
                                                    result_dir_tmp):
        '''
        '''
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def extract_statement_coverage_data_of_a_test(self, result_dir_tmp):
        '''
            return: the dict of statements with covering count
        '''
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def extract_branch_coverage_data_of_a_test(self, result_dir_tmp):
        '''
            return: the dict of branches with covering count
        '''
        print ("!!! Must be implemented in child class !!!")

    @abc.abstractmethod
    def extract_function_coverage_data_of_a_test(self, result_dir_tmp):
        '''
            return: the dict of functions with covering count
        '''
        print ("!!! Must be implemented in child class !!!")


    def runtests_code_coverage (self, testcases, criterion_to_matrix,
                                                    re_instrument_code=True):

        enabled_criteria_matrices = {}
        for criterion in criterion_to_matrix:
            if criterion_to_matrix[criterion] is not None:
                enabled_criteria_matrices[criterion] = \
                                                criterion_to_matrix[criterion]

        assert len(enabled_criteria_matrices) > 0, "no criterion enabled"

        assert len(set(enabled_criteria_matrices) - \
                            set(self.getSupportedCriteria())) == 0, \
                                        "Some unsuported criteria are enabled"

        criterion_to_enabling = {}
        for criterion in self.getSupportedCriteria():
            criterion_to_enabling[criterion] = \
                                    (criterion in enabled_criteria_matrices)

        # Check that the result_matrix is empty and fine
        for criterion in enabled_criteria_matrices:
            assert enabled_criteria_matrices[criterion].is_empty(), "the matrix must be empty"
            assert set(testcases) == 
                        set(enabled_criteria_matrices[criterion].get_nonkey_colname_list()),
                "The specified test cases are not same in the matrix"

        # Intrument the codes and get instrumented executables
        if re_instrument_code:
            criterion2executable_path = self.instrument_code( \
                                criterion_to_enabling=criterion_to_enabling)
        else:
            criterion2executable_path = \
                self.get_instrumented_executable_paths(criterion_to_enabling)

        # get environment vars
        result_dir_tmp = os.path.join(self.codecoverage_working_dir, \
                                            "codecoverage_meta_result_tmp")
        if os.isdir(result_dir_tmp):
            shutil.rmtree(result_dir_tmp)

        criterion2environment_vars = self.get_codecoverage_environment_vars( \
                                                            result_dir_tmp, \
                                criterion_to_enabling=criterion_to_enabling)

        assert set(criterion2executable_path) == \
                    set(criterion2environment_vars), \
                            "mismatch between exe_path and env_vars"

        criterialist = criterion2executable_path.keys()

        # separate to common executions (those with same exe_path and env_vars)
        # XXX
        groups = []
        for c_pos, criterion in enumerate(criterialist):
            found = False
            for g in groups:
                if criterion in g['critera']:
                    found = True
                    break
            if not found:
                # add its group
                groups.append({'criteria':[criterion], 
                            'exe_path': criterion2executable_path[criterion],
                            'env_vars': criterion2environment_vars[criterion]
                            })
                # add anyone else from same group
                for e_pos in range(c_pos+1, len(criterialist)):
                    if criterion2executable_path[criterialist[e_pos]] == \
                                            groups[-1]['exe_path'] and \
                            criterion2environment_vars[criterialist[e_pos]] == \
                                                        groups[-1]['env_vars']:
                       groups[-1]['criteria'].append(criterialist[e_pos]) 

        # Execute each test and gather the data
        criterion2coverage_per_test = {criterion: {} for criterion in criterialist}
        for testcase in testcases:
            for c_group in groups:
                # Create reult_tmp_dir
                os.mkdir(result_dir_tmp)

                # run testcase
                verdict = self.meta_test_generation_obj.execute_testcase (testcase,
                                        exe_path=c_group['exe_path'], 
                                        env_vars=c_group['env_vars'])
                
                # Collect temporary data into result_dir_tmp
                self.collect_temporary_coverage_data(c_group['criteria'], \
                                                    c_group['env_vars'], \
                                                            result_dir_tmp)

                # extract coverage
                for criterion in c_group['criteria']:
                    if criterion == STATEMENT_KEY:
                        coverage_tmp_data = self.extract_statement_coverage_data_of_a_test(result_dir_tmp)
                    elif criterion == BRANCH_KEY:
                        coverage_tmp_data = self.extract_branch_coverage_data_of_a_test(result_dir_tmp)
                    elif criterion == FUNCTION_KEY:
                        coverage_tmp_data = self.extract_function_coverage_data_of_a_test(result_dir_tmp)
                    else:
                        assert False, "Invalid criterion: "+criterion

                    if len(criterion2coverage_per_test[criterion]) == 0:
                        for elem in coverage_tmp_data:
                            criterion2coverage_per_test[criterion][elem] = {}

                    for elem in coverage_tmp_data:
                        # verify that the value is positive or null
                        assert type(coverage_tmp_data[elem]) == int, \
                                                    "cov num type must be int"
                        assert coverage_tmp_data[elem] >= 0, \
                                                "invalid cov num(negative)"
                        criterion2coverage_per_test[criterion][elem][testcase] =\
                                                        coverage_tmp_data[elem]

                # remove dir created for temporal storage
                shutil.rmtree(result_dir_tmp)

        # Write the execution data into the matrices
        # Since for ExecutionMatrix, active is not 0 thus this is direct.
        for criterion in criterion2coverage_per_test:
            for key in criterion2coverage_per_test[criterion]:
                enabled_criteria_matrices[criterion].\
                                            add_row_by_key(key, \
                            criterion2coverage_per_test[criterion][key], \
                                                            serialize=False)
            # Serialize to disk
            enabled_criteria_matrices[criterion].serialize()


    def instrument_code (self, outputdir=None, code_builder_override=None,
                                                    criterion_to_enabling)
        '''
        '''
        assert len[x for x in criterion_to_enabling \
                                        if criterion_to_enabling[x]] > 0, \
                                                    "no criterion is enabled"

        if outputdir is None:
            outputdir = self.instrumented_code_storage_dir
        
        if os.path.isdir(outputdir):
            shutil.rmtree(outputdir)
        os.mkdir(outputdir)

        if code_builder_override is None:
            code_builder_override = self.code_builder

        self.do_instrument_code (outputdir=outputdir, 
                                    code_builder=code_builder_override,
                                    criterion_to_enabling)
        return self.get_instrumented_executable_paths(criterion_to_enabling)
        
    @abc.abstractmethod
    def do_instrument (self, outputdir, code_builder, criterion_to_enabling):
        print ("!!! Must be implemented in child class !!!")

