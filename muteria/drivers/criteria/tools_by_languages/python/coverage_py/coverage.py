
from __future__ import print_function

import os
import sys
import re
import shutil
import glob
import logging
import configparser

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

from muteria.repositoryandcode.codes_convert_support import CodeFormats
from muteria.repositoryandcode.callback_object import DefaultCallbackObject

from muteria.drivers.criteria.base_testcriteriatool import BaseCriteriaTool
from muteria.drivers.criteria import TestCriteria
from muteria.drivers import DriversUtils

import coverage

ERROR_HANDLER = common_mix.ErrorHandler

class CriteriaToolCoveragePy(BaseCriteriaTool):
    def __init__(self, *args, **kwargs):
        BaseCriteriaTool.__init__(self, *args, **kwargs)
        self.instrumentation_details = os.path.join(\
                    self.instrumented_code_storage_dir, '.instru.meta.json')
        self.cov_data_filename = "cov_data.json"
        self.used_srcs_dir = os.path.join(self.instrumented_code_storage_dir,\
                                                            'used_srcs_dir')
        self.preload_dir = os.path.join(self.instrumented_code_storage_dir,\
                                                                'config_dir')
        self.preload_file = os.path.join(self.preload_dir, 'usercutomize.py')
        self.config_file = os.path.join(self.instrumented_code_storage_dir,\
                                                                '.configrc')
        self.raw_data_file = os.path.join(self.instrumented_code_storage_dir,\
                                                                    '.rawdata')
        # clean any possible raw data file
        for file_ in glob.glob(self.raw_data_file+"*"):
            os.remove(file_)
    #~ def __init__()

    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        try:
            import coverage
        except ImportError:
            return False
        #for prog in ('coverage'):
        #    if not DriversUtils.check_tool(prog=prog, args_list=['--version'],\
        #                                            expected_exit_codes=[0]):
        #        return False
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
               ]
    #~ def _get_meta_instrumentation_criteria()

    @classmethod
    def _get_separated_instrumentation_criteria(cls):
        """ Criteria where all elements are instrumented in different files
            :return: list of citeria
        """
        return []
    #~ def _get_separated_instrumentation_criteria()

    def get_instrumented_executable_paths(self, enabled_criteria):
        crit_to_exes_map = {}
        obj = common_fs.loadJSON(self.instrumentation_details)
        exes = [p for _, p in list(obj.items())]
        for criterion in enabled_criteria:
            crit_to_exes_map[criterion] = exes
        return crit_to_exes_map
    #~ def get_instrumented_executable_paths()

    def _get_criterion_element_executable_path(self, criterion, element_id):
        ERROR_HANDLER.error_exit("not applicable for coverage_py", __file__)
    #~ def _get_criterion_element_executable_path

    def _get_criterion_element_environment_vars(self, criterion, element_id):
        '''
            return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        ERROR_HANDLER.error_exit("not applicable for coverage_py", __file__)
    #~ def _get_criterion_element_environment_vars()

    def _get_criteria_environment_vars(self, result_dir_tmp, enabled_criteria):
        '''
        return: python dictionary with environment variable as key
                     and their values as value (all strings)
        '''
        return {
                    "PYTHONUSERBASE": self.preload_dir, 
                    "COVERAGE_PROCESS_START": self.config_file,
                }
    #~ def _get_criteria_environment_vars()

    class PathAliases(object):
        def __init__(self, data_files, exe_rel_files, inst_top_dir):
            self.alias_map = {}
            a_data_file = os.path.normpath(data_files[0])
            prefix = None
            for fn in exe_rel_files:
                if a_data_file.endswith(fn):
                    prefix = a_data_file[:-len(fn)]
            ERROR_HANDLER.assert_true(prefix is not None, \
                        "file in data has no match in source", __file__)
            for i in range(len(data_files)):
                self.alias_map[data_files[i]] = os.path.join(\
                                                        inst_top_dir, \
                            os.path.normpath(data_files[i])[len(prefix):])
        def map(self, in_dat_file):
            return self.alias_map[in_dat_file]
    #~ PathAliases

    def _collect_temporary_coverage_data(self, criteria_name_list, \
                                            test_execution_verdict, \
                                            used_environment_vars, \
                                                    result_dir_tmp):
        ''' extract coverage data into json file in result_dir_tmp
        '''
        cov_obj = coverage.Coverage(config_file=self.config_file)
        cov_obj.combine()
        tmp_dat_obj = cov_obj.get_data()
        
        in_dat_files = tmp_dat_obj.measured_files()

        # Get file map
        try :
            self.exes_rel
        except:
            obj = common_fs.loadJSON(self.instrumentation_details)
            self.exes_abs = []
            self.exes_rel = []
            for rp, ap in list(obj.items()):
                self.exes_rel = rp
                self.exes_abs = ap
            self.exes_rel.sort(reverse=True,key=lambda x: x.count(os.path.sep))
        

        dat_obj = coverage.CoverageData()
        file_map = self.PathAliases(in_dat_files, self.exes_rel, \
                                                            self.used_srcs_dir)
        dat_obj.update(tmp_dat_obj, aliases=file_map)

        # Get the coverages
        res = {c: {} for c in criteria_name_list}
        if TestCriteria.STATEMENT_COVERAGE in criteria_name_list:
            for fi in range(len(self.exes_abs)):
                res[TestCriteria.STATEMENT_COVERAGE][self.exes_rel[fi]] = \
                                            dat_obj.lines(self.exes_abs[fi])
        if TestCriteria.BRANCH_COVERAGE in criteria_name_list:
            for fi in range(len(self.exes_abs)):
                res[TestCriteria.BRANCH_COVERAGE][self.exes_rel[fi]] = \
                                                dat_obj.arcs(self.exes_abs[fi])

        # save the temporary coverage
        common_fs.dumpJSON(res, os.path.join(result_dir_tmp,\
                                                    self.cov_data_filename))

        cov_obj.erase()
        # clean any possible raw data file
        for file_ in glob.glob(self.raw_data_file+"*"):
            os.remove(file_)
    #~ def _collect_temporary_coverage_data()

    def _extract_coverage_data_of_a_test(self, enabled_criteria, \
                                    test_execution_verdict, result_dir_tmp):
        ''' read json files and extract data
            return: the dict of criteria with covering count
        '''
        in_file = os.path.join(result_dir_tmp, self.cov_data_filename)
        cov_dat_obj = common_fs.loadJSON(in_file)
        
        ERROR_HANDLER.assert_true(set(cov_dat_obj) == set(enabled_criteria), \
                                    "mismatching criteria enabled", __file__)

        res = {c: {} for c in enabled_criteria}

        for c in cov_dat_obj:
            for filename in cov_dat_obj[c]:
                for id_ in cov_dat_obj[c][filename]:
                    ident = DriversUtils.make_meta_element(id_, filename)
                    res[c][ident] = 1

        # delete cov file
        os.remove(in_file)

        return res
    #~ def _extract_coverage_data_of_a_test()

    def _do_instrument_code (self, outputdir, exe_path_map, \
                                        code_builds_factory, \
                                        enabled_criteria, parallel_count=1):
        # Setup
        if os.path.isdir(self.instrumented_code_storage_dir):
            shutil.rmtree(self.instrumented_code_storage_dir)
        os.mkdir(self.instrumented_code_storage_dir)
        if os.path.isdir(self.used_srcs_dir):
            shutil.rmtree(self.used_srcs_dir)
        os.mkdir(self.used_srcs_dir)
        if os.path.isdir(self.preload_dir):
            shutil.rmtree(self.preload_dir)
        os.mkdir(self.preload_dir)

        rel_path_map = {}
        exes, _ = code_builds_factory.repository_manager.\
                                                    get_relative_exe_path_map()
        for exe in exes:
            rel_path_map[exe] = os.path.join(self.used_srcs_dir, exe)
            relloc = os.path.join(self.used_srcs_dir, os.path.dirname(exe))
            if not os.path.isdir(relloc):
                os.makedirs(relloc)
        ret = code_builds_factory.transform_src_into_dest(\
                        src_fmt=CodeFormats.PYTHON_SOURCE,\
                        dest_fmt=CodeFormats.PYTHON_SOURCE,\
                        src_dest_files_paths_map=rel_path_map)
        # write down the rel_path_map
        ERROR_HANDLER.assert_true(not os.path.isfile(\
                self.instrumentation_details), "must not exist here", __file__)
        common_fs.dumpJSON(rel_path_map, self.instrumentation_details)

        if not ret:
            ERROR_HANDLER.error_exit("Problem with copying python sources", \
                                                                    __file__)

        # Create config and preload
        with open(self.preload_file, "w") as f:
            f.write("import coverage\ncoverage.process_startup()\n")
        config = configparser.ConfigParser()
        config['run'] = {'ServerAliveInterval': '45',
                        'include': rel_path_map.keys(),
                        'data_file': self.raw_data_file,
                        'branch': (\
                            TestCriteria.BRANCH_COVERAGE in enabled_criteria),
                        'parallel': True,
                        'concurrency': ['thread', 'multiprocessing', \
                                            'gevent', 'greenlet', 'eventlet'],
                        }
        with open(self.config_file, 'w') as f:
            config.write(f)
    #~ def _do_instrument_code()
#~ class CriteriaToolCoveragePy