#
# [LICENCE]
#
""" Code coverage tool module. The class of interest is BaseCOdecoverageTool.

The tools are organized by programming language

For each language, there is a folder for each tool, 
named after the tool in all lowercase , starting with letter or underscore(_),
The remaining caracters are either letter, number or underscore

XXX Each codecoverage tool package must have the 
following in the __init__.py file:
>>> import <Module>.<class extending BaseCodecoverageTool> as CodecoverageTool
"""

from __future__ import print_function
import os
import sys
import glob
import shutil
import logging
import abc

import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

from muteria.drivers.checkpoint_handler import CheckPointHandler
from muteria.drivers.codecoverage import CodecoverageType

ERROR_HANDLER = common_mix.ErrorHandler

class BaseCodecoverageTool(abc.ABC):
    '''
    '''
    @abc.abstractclassmethod
    @classmethod
    def installed(cls):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        print ("!!! Must be implemented in child class !!!")

    def __init__(self, meta_test_generation_obj, codecoverage_working_dir, 
                                code_builds_factory, config, checkpointer):
        # Set Constants
        
        # Set Direct Arguments Variables
        self.meta_test_generation_obj = meta_test_generation_obj
        self.codecoverage_working_dir = codecoverage_working_dir
        self.code_builds_factory = code_builds_factory
        self.config = config
        self.checkpointer = checkpointer
        
        # Verify Direct Arguments Variables
        ERROR_HANDLER.assert_true(self.codecoverage_working_dir is None, \
                            "Must specify codecoverage_working_dir", __file__)
        
        # Set Indirect Arguments Variables
        ## put the instrumented code into this folder (to be created by user)
        self.instrumented_code_storage_dir = os.path.join(
                        self.codecoverage_working_dir, "instrumented_code")
        
        # Verify indirect Arguments Variables
        
        # Initialize Other Fields
        
        # Make Initialization Computation
        ## Create dirs
        if not os.path.isdir(self.codecoverage_working_dir):
            os.mkdir(self.codecoverage_working_dir)

    #~ def __init__()

    def get_checkpointer(self):
        return self.checkpointer
    #~ def get_checkpointer()

    def has_checkpointer(self):
        return self.checkpointer is not None
    #~ def has_checkpointer()

    @abc.abstractmethod
    @classmethod
    def get_supported_criteria(cls):
        #return [CodecoverageType.STATEMENT_KEY, CodecoverageType.BRANCH_KEY, \
        #                                      CodecoverageType.FUNCTION_KEY]
        print ("!!! Must be implemented in child class !!!")
    #~ def get_supported_criteria()

    @abc.abstractmethod
    def get_instrumented_executable_paths(self, criterion_to_enabling):
        print ("!!! Must be implemented in child class !!!")
    #~ def get_instrumented_executable_paths()

    @abc.abstractmethod
    def _get_codecoverage_environment_vars(self, result_dir_tmp, \
                                                    criterion_to_enabling):
        '''
        return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _get_codecoverage_environment_vars()

    @abc.abstractmethod
    def _collect_temporary_coverage_data(self, criteria_name_list, \
                                            used_environment_vars, \
                                                    result_dir_tmp):
        '''
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _collect_temporary_coverage_data()

    @abc.abstractmethod
    def _extract_statement_cov_data_of_a_test(self, result_dir_tmp):
        '''
            return: the dict of statements with covering count
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _extract_statement_cov_data_of_a_test()

    @abc.abstractmethod
    def _extract_branch_cov_data_of_a_test(self, result_dir_tmp):
        '''
            return: the dict of branches with covering count
        '''
        print ("!!! Must be implemented in child class !!!")
    #~ def _extract_branch_cov_data_of_a_test()

    @abc.abstractmethod
    def _extract_function_cov_data_of_a_test(self, result_dir_tmp):
        '''
            return: the dict of functions with covering count
        '''
        print ("!!! Must be implemented in child class !!!")
    #~def _extract_function_cov_data_of_a_test()

    def runtests_criteria_coverage (self, testcases, criterion_to_matrix,
                            re_instrument_code=True, test_parallel_count=1):
        """
            (TODO: support parallelism: per test outdata)
        """
        # FIXME: Support parallelism, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(test_parallel_count <= 1, \
                "FIXME: Must first implement support for parallel mutatio")
        #~ FXIMEnd

        # @Checkpoint: create a checkpoint handler (for time)
        checkpoint_handler = CheckPointHandler(self.get_checkpointer())
        if checkpoint_handler.is_finished():
            return

        enabled_criteria_matrices = {}
        for criterion in criterion_to_matrix:
            if criterion_to_matrix[criterion] is not None:
                enabled_criteria_matrices[criterion] = \
                                                criterion_to_matrix[criterion]

        ERROR_HANDLER.assert_true(len(enabled_criteria_matrices) > 0, \
                                            "no criterion enabled", __file__)

        ERROR_HANDLER.assert_true(len(set(enabled_criteria_matrices) - \
                                set(self.get_supported_criteria())) == 0, \
                            "Some unsuported criteria are enabled", __file__)

        criterion_to_enabling = {}
        for criterion in self.get_supported_criteria():
            criterion_to_enabling[criterion] = \
                                    (criterion in enabled_criteria_matrices)

        # Check that the result_matrix is empty and fine
        for criterion in enabled_criteria_matrices:
            ERROR_HANDLER.assert_true( \
                            enabled_criteria_matrices[criterion].is_empty(), \
                                          "the matrix must be empty", __file__)

            ERROR_HANDLER.assert_true( \
                    set(testcases) == set(enabled_criteria_matrices[criterion]\
                                                .get_nonkey_colname_list()), \
                        "The specified test cases are not same in the matrix",
                                                                    __file__)

        # Intrument the codes and get instrumented executables
        if re_instrument_code:
            criterion2executable_path = self.instrument_code( \
                                enabled_criteria=criterion_to_enabling)
        else:
            criterion2executable_path = \
                self.get_instrumented_executable_paths(criterion_to_enabling)

        # get environment vars
        result_dir_tmp = os.path.join(self.codecoverage_working_dir, \
                                                "codecoverage_meta_result_tmp")
        if os.path.isdir(result_dir_tmp):
            shutil.rmtree(result_dir_tmp)

        criterion2environment_vars = self._get_codecoverage_environment_vars( \
                                                            result_dir_tmp, \
                                criterion_to_enabling=criterion_to_enabling)

        assert set(criterion2executable_path) == \
                    set(criterion2environment_vars), \
                            "mismatch between exe_path_map and env_vars"

        criterialist = criterion2executable_path.keys()

        # separate to common executions 
        # (those with same exe_path_map and env_vars)
        # XXX
        groups = []
        for c_pos, criterion in enumerate(criterialist):
            found = False
            for g in groups:
                if criterion in g['criteria']:
                    found = True
                    break
            if not found:
                # add its group
                groups.append({'criteria':[criterion], 
                        'exe_path_map': criterion2executable_path[criterion],
                        'env_vars': criterion2environment_vars[criterion]
                        })
                # add anyone else from same group
                for e_pos in range(c_pos+1, len(criterialist)):
                    if criterion2executable_path[criterialist[e_pos]] == \
                                            groups[-1]['exe_path_map'] and \
                            criterion2environment_vars[criterialist[e_pos]] ==\
                                                        groups[-1]['env_vars']:
                       groups[-1]['criteria'].append(criterialist[e_pos]) 

        # Execute each test and gather the data
        criterion2coverage_per_test = \
                                {criterion: {} for criterion in criterialist}
        for testcase in testcases:
            for c_group in groups:
                # Create reult_tmp_dir
                os.mkdir(result_dir_tmp)

                # run testcase
                self.meta_test_generation_obj.execute_testcase (testcase, \
                                        exe_path_map=c_group['exe_path_map'], \
                                        env_vars=c_group['env_vars'])
                
                # Collect temporary data into result_dir_tmp
                self._collect_temporary_coverage_data(c_group['criteria'], \
                                                    c_group['env_vars'], \
                                                            result_dir_tmp)

                # extract coverage
                for criterion in c_group['criteria']:
                    if criterion == CodecoverageType.STATEMENT_KEY:
                        coverage_tmp_data = \
                                self._extract_statement_cov_data_of_a_test( \
                                                                result_dir_tmp)
                    elif criterion == CodecoverageType.BRANCH_KEY:
                        coverage_tmp_data = \
                                self._extract_branch_cov_data_of_a_test( \
                                                                result_dir_tmp)
                    elif criterion == CodecoverageType.FUNCTION_KEY:
                        coverage_tmp_data = \
                                self._extract_function_cov_data_of_a_test( \
                                                                result_dir_tmp)
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
                        criterion2coverage_per_test[criterion][elem][testcase]\
                                                    = coverage_tmp_data[elem]

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

        # @Checkpoint: Finished (for time)
        checkpoint_handler.set_finished(None)
    #~ def runtests_criteria_coverage()

    def instrument_code (self, enabled_criterion, outputdir=None, \
                        code_builds_factory_override=None, parallel_count=1):
        '''
            (TODO: support parallelism: per test outdata)
        '''
        # FIXME: Support parallelism, then remove the code
        # bellow:
        ERROR_HANDLER.assert_true(parallel_count <= 1, \
                "FIXME: Must first implement support for parallel mutatio")
        #~ FXIMEnd

        # @Checkpoint: create a checkpoint handler (for time)
        checkpoint_handler = CheckPointHandler(self.get_checkpointer())
        if not checkpoint_handler.is_finished():

            ERROR_HANDLER.assert_true(len([x for x in criterion_to_enabling \
                                        if criterion_to_enabling[x]]) > 0, \
                                        "no criterion is enabled", __file__)

            if outputdir is None:
                outputdir = self.instrumented_code_storage_dir
            
            if os.path.isdir(outputdir):
                shutil.rmtree(outputdir)
            os.mkdir(outputdir)

            if code_builds_factory_override is None:
                code_builds_factory_override = self.code_builds_factory

            self._do_instrument_code (outputdir=outputdir, \
                            code_builds_factory=code_builds_factory_override, \
                                criterion_to_enabling=criterion_to_enabling)

            # @Checkpoint: Finished (for time)
            checkpoint_handler.set_finished(None)

        return self.get_instrumented_executable_paths(criterion_to_enabling)
    #~ def instrument_code()
        
    @abc.abstractmethod
    def _do_instrument_code (self, outputdir, code_builds_factory, \
                                                        criterion_to_enabling):
        print ("!!! Must be implemented in child class !!!")
    #~ def do_instrument()
