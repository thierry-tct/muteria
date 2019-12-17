"""
TODO: Add support for multi versions of results 
"""

from __future__ import print_function

import os 
import logging
import shutil
import glob
import math
import copy
import random

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

from muteria.repositoryandcode.repository_manager import RepositoryManager
from muteria.repositoryandcode.code_builds_factory import CodeBuildsFactory

from muteria.drivers import DriversUtils
from muteria.drivers.testgeneration import TestToolType
from muteria.drivers.testgeneration.meta_testcasetool import MetaTestcaseTool
import muteria.drivers.criteria as criteria_pkg
from muteria.drivers.criteria.meta_testcriteriatool import MetaCriteriaTool

import muteria.drivers.optimizers.criteriatestexecution.optimizerdefs as \
                                                                crit_opt_module

from muteria.statistics.main import StatsComputer

import muteria.controller.explorer as outdir_struct
import muteria.controller.logging_setup as logging_setup
import muteria.controller.checkpoint_tasks as checkpoint_tasks

ERROR_HANDLER = common_mix.ErrorHandler

class CheckpointData(dict):
    """
    """
    def __init__(self):
        pass
    #~ def __init__()

    def update_all(self, tasks_obj, test_types, test_types_pos, \
                                criteria_set, criteria_set_pos):
        self.update_tasks_obj(tasks_obj)
        self.update_test_types(test_types_pos, test_types)
        self.update_criteria_set(criteria_set_pos, criteria_set)
    #~ def update_all()

    def get_json_obj(self):
        retval = dict(self.__dict__)
        retval['tasks_obj'] = retval['tasks_obj'].get_as_json_object()
        retval['test_types'] = [tt.get_str() for tt in retval['test_types']]
        if self.criteria_set is not None:
            retval['criteria_set'] = \
                                [c.get_str() for c in retval['criteria_set']]
        return retval
    #~ def get_json_obj()

    def update_from_json_obj(self, json_obj):
        self.update_all(**json_obj)
        self.tasks_obj = checkpoint_tasks.TaskOrderingDependency(\
                                                    json_obj=self.tasks_obj)
        self.test_types = tuple([TestToolType[tt] for tt in self.test_types])
        if self.criteria_set is not None:
            self.criteria_set = set(\
                    [criteria_pkg.TestCriteria[c] for c in self.criteria_set])
    #~ def update_from_json_obj()

    def test_tool_types_is_executed(self, seq_id, test_tool_types):
        if self.test_types_pos > seq_id:
            return True
        if self.test_types_pos == seq_id and \
                                set(self.test_types) != set(test_tool_types):
            ERROR_HANDLER.error_exit("cp test_tool_type changed", __file__)
        return False
    #~ def test_tool_types_is_executed()

    def switchto_new_test_tool_types(self, seq_id, test_tool_types):
        if seq_id > self.test_types_pos:
            self.tasks_obj.set_task_back_as_todo_executing(\
                            checkpoint_tasks.Tasks.TESTS_GENERATION_GUIDANCE)
            self.update_test_types(seq_id, test_tool_types)
            self.update_criteria_set(None, None)
    #~ def switchto_new_test_tool_types()

    def criteria_set_is_executed(self, seq_id, criteria_set):
        if self.criteria_set_pos is not None:
            if self.criteria_set_pos > seq_id:
                return True
            if self.criteria_set_pos == seq_id:
                ERROR_HANDLER.assert_true(set(self.criteria_set) \
                                                        == set(criteria_set), \
                                        "cp criteria_set changed", __file__)
                return True
        return False
    #~ def criteria_set_is_executed()

    def switchto_new_criteria_set(self, seq_id, criteria_set):
        if self.criteria_set_pos is None or seq_id > self.criteria_set_pos:
            self.update_criteria_set(seq_id, criteria_set)
    #~ def switchto_new_criteria_set()

    def update_tasks_obj(self, tasks_obj):
        self.tasks_obj = tasks_obj
    #~ def update_tasks_obj()

    def update_test_types(self, test_types_pos, test_types):
        self.test_types = test_types
        self.test_types_pos = test_types_pos
    #~ def update_test_types()
        
    def update_criteria_set(self, criteria_set_pos, criteria_set):
        self.criteria_set = criteria_set
        self.criteria_set_pos = criteria_set_pos
    #~ def update_criteria_set()
#~ class CheckpointData

class Executor(object):
    """ Execution Orchestration class
        The execution entry point is the method 'main' 
    """

    def __init__(self, config, top_timeline_explorer):
        """ The various configurations for the execution are passed here, as
            well as the corresponding directory structure
        """
        self.config = config
        self.top_timeline_explorer = top_timeline_explorer

        self.head_explorer = self.top_timeline_explorer.get_latest_explorer()
        # Initialize output structure
        self._initialize_output_structure(cleanstart=\
                                self.config.EXECUTION_CLEANSTART.get_val())
        if not logging_setup.is_setup():
            if self.config.LOG_DEBUG.get_val():
                logging_setup.setup(file_level=logging.DEBUG, \
                            console_level=logging.DEBUG, \
                            logfile=self.head_explorer.get_file_pathname(\
                                                outdir_struct.MAIN_LOG_FILE))
                logging.debug("Logging Debug Level")
            else:
                logging_setup.setup(\
                            logfile=self.head_explorer.get_file_pathname(\
                                                outdir_struct.MAIN_LOG_FILE))
        # Create repo manager
        # XXX The repo manager automatically revert any previous problem
        self.repo_mgr = Executor.create_repo_manager(config)

        # set error handlers for revert repo
        common_mix.ErrorHandler.set_corresponding_repos_manager(self.repo_mgr)

        # create codes builders
        self.cb_factory = CodeBuildsFactory(self.repo_mgr, \
                                workdir=self.head_explorer.get_file_pathname(\
                                            outdir_struct.CB_FACTORY_WORKDIR))
    #~ def __init__()

    def main(self):
        """ Executor entry point
        """
        # Initialize output structure (done in __init__)
        #self._initialize_output_structure(\
        #                cleanstart=self.config.EXECUTION_CLEANSTART.get_val())

        # Make checkpointer
        self.checkpointer = \
                    common_fs.CheckpointState(*self._get_checkpoint_files())
        was_finished = False
        if self.checkpointer.is_finished():
            if len(self.config.RE_EXECUTE_FROM_CHECKPOINT_META_TASKS.\
                                                                get_val()) > 0:
                self.checkpointer.restart_task()
                was_finished = True
            else:
                return

        # Meta testcases tool
        self.meta_testcase_tool = self._create_meta_test_tool(self.config, \
                                                            self.head_explorer)
        self.meta_testcase_tool.check_tools_installed()

        # Meta criteria
        self.meta_criteria_tool = self._create_meta_criteria_tool(self.config,\
                                                    self.meta_testcase_tool)
        self.meta_criteria_tool.check_tools_installed()

        # Test generation guidance
        self.meta_testgen_guidance_tool = self._create_meta_testgen_guidance(\
                                                                self.config)

        # Test execution optimization
        self.meta_testexec_optimization_tool = \
                        self._create_meta_testexec_optimization(self.config)

        # Criteria generation guidance
        self.meta_criteriagen_guidance_tool = \
                            self._create_meta_criteriagen_guidance(self.config)

        # Criteria optimization
        self.meta_criteriaexec_optimization_tools = \
                    self._create_meta_criteriaexec_optimization(self.config)

        # See whether starting or continuing
        check_pt_obj = self.checkpointer.load_checkpoint_or_start(\
                                            ret_detailed_exectime_obj=False)
        
        test_tool_type_sequence = \
                            self.config.TEST_TOOL_TYPES_SCHEDULING.get_val()

        # Do nothing if no tool types specified
        if len(test_tool_type_sequence) == 0:
            return
            
        self.cp_data = CheckpointData()
        if check_pt_obj is not None:
            # Continuing
            self.cp_data.update_from_json_obj(json_obj=check_pt_obj)
        else:
            # Staring anew
            self.cp_data = CheckpointData()
            self.cp_data.update_all(\
                        tasks_obj=checkpoint_tasks.TaskOrderingDependency(),\
                        test_types=test_tool_type_sequence[0],\
                        test_types_pos=0,\
                        criteria_set=None,\
                        criteria_set_pos=None)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

        # Ensure that the repository exe and obj are in default state
        self.cb_factory.set_repo_to_build_default()

        # Execute the tasks
        task_set = None
        # by testtool type sequence loop
        for seq_id, test_tool_types in enumerate(test_tool_type_sequence):
            
            logging.info("")
            logging.info("executor: Running for Test tool types = "+\
                                str([t.get_str() for t in test_tool_types]))
            logging.info("")

            # Was it already checkpointed w.r.t test type seq
            if self.cp_data.test_tool_types_is_executed(\
                                                    seq_id, test_tool_types):
                continue

            #if len(self.meta_testcase_tool.get_candidate_tools_aliases(\
            #                        test_tool_type_list=test_tool_types)) == 0:
            #   continue
            
            # If we have a new seq_id, it is another test type loop
            # NOTE: This switch is written at following steps (tasks...)
            self.cp_data.switchto_new_test_tool_types(seq_id, test_tool_types)

            # Actual Execution in the temporary dir (until before finish)
            while True:
                # (Break flow)
                if len(self.config.RE_EXECUTE_FROM_CHECKPOINT_META_TASKS.\
                                                                get_val()) > 0:
                    if was_finished:
                        # XXX: go to the state right before finished is set
                        self.cp_data.tasks_obj.set_all_tasks_to_completed()
                    for task in self.config\
                                        .RE_EXECUTE_FROM_CHECKPOINT_META_TASKS\
                                        .get_val():
                        self.cp_data.tasks_obj\
                                        .set_task_back_as_todo_untouched(task)
                    self.config.RE_EXECUTE_FROM_CHECKPOINT_META_TASKS\
                                                                .set_val([])

                # 1. get executing task
                task_set = self.cp_data.tasks_obj.get_next_todo_tasks()

                # 2. stop if the next task is FINISHED
                if len(task_set) == 0 or (len(task_set) == 1 and \
                        list(task_set)[0] == checkpoint_tasks.Tasks.FINISHED):
                    break

                # 3. stop if the next task is AGGREGATED_STATS and there 
                # is still iteration from test_tool_type_sequence
                if (len(task_set) == 1 \
                                and list(task_set)[0] == \
                                    checkpoint_tasks.Tasks.AGGREGATED_STATS \
                                and seq_id < len(test_tool_type_sequence) - 1):
                    break

                # (Break flow)
                # use the rerun from here, only here, stop after here
                if self.config.RESTART_CURRENT_EXECUTING_META_TASKS.get_val():
                    # restarts the tasks
                    for task in task_set:
                        self.cp_data.tasks_obj.\
                                        set_task_back_as_todo_untouched(task)
                    # disable it
                    self.config.RESTART_CURRENT_EXECUTING_META_TASKS.set_val(\
                                                                        False)
                    
                
                # 3. execute the tasks  (TODO: parallelism)
                for task in task_set:
                    self._execute_task(task)

                # (Break flow)
                if self.config.EXECUTE_ONLY_CURENT_CHECKPOINT_META_TASK.\
                                                                    get_val():
                    ERROR_HANDLER.error_exit("(DBG) Stopped after executing"
                                " only the current checkpoint meta tasks."
                                " because of corresponding variable was set", \
                                                                    __file__)

        ERROR_HANDLER.assert_true(task_set is not None, \
                "There must be task set (empty list or FINISHED)", __file__)

        # Set checkpoint to finished
        if len(task_set) == 1:
            ERROR_HANDLER.assert_true(list(task_set)[0] == \
                                            checkpoint_tasks.Tasks.FINISHED,\
                                        "task must be Finished Here", __file__)
            self.cp_data.tasks_obj.set_task_completed(list(task_set)[0])
        else:
            ERROR_HANDLER.assert_true(len(task_set) == 0, \
                                    "task set must be empty here", __file__)

        self.checkpointer.set_finished()
    #~ def main()

    def get_repo_manager(self):
        return self.repo_mgr
    #~ def get_repo_manager()

    def _execute_task(self, task):
        """ TODO: 
                1. implement the todos here
        """
        
        # @Checkpointing: see whether the task is untouch to clear tmp
        task_untouched = self.cp_data.tasks_obj.task_is_untouched(task)

        # Execute base on the task: ---------------------------------------
        if task == checkpoint_tasks.Tasks.STARTING:
            pass
        elif task == checkpoint_tasks.Tasks.FINISHED:
            pass

        elif task == checkpoint_tasks.Tasks.TESTS_GENERATION_GUIDANCE:
            pass #TODO: Generate focus criteria and tests and store in json file
        elif task == checkpoint_tasks.Tasks.TESTS_GENERATION:
            # @Checkpointing
            if task_untouched:
                #if self.cp_data.test_types_pos == 0:
                #    self.meta_testcase_tool.clear_working_dir() 
                if self.meta_testcase_tool.has_checkpointer():
                    self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            # Generate the tests without criteria instrumented
            self.meta_testcase_tool.generate_tests(\
                            meta_criteria_tool_obj=None, \
                            test_tool_type_list=self.cp_data.test_types)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())
            # Destroy meta test checkpointer
            self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

        elif task == checkpoint_tasks.Tasks.TESTS_GENERATION_USING_CRITERIA:
            # @Checkpointing
            if task_untouched:
                #if self.cp_data.test_types_pos == 0:
                #    self.meta_testcase_tool.clear_working_dir() 
                if self.meta_testcase_tool.has_checkpointer():
                    self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            # Generate the tests using criteria
            self.meta_testcase_tool.generate_tests(\
                            meta_criteria_tool_obj=self.meta_criteria_tool, \
                            test_tool_type_list=self.cp_data.test_types)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())
            # Destroy meta test checkpointer
            self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

        elif task == checkpoint_tasks.Tasks.\
                                    TESTS_EXECUTION_SELECTION_PRIORITIZATION:
            out_file_key = outdir_struct.TMP_SELECTED_TESTS_LIST
            out_file = self.head_explorer.get_file_pathname(out_file_key)
                                        
            # @Checkpointing
            if task_untouched:
                if self.meta_testcase_tool.has_checkpointer():
                    self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()
                self.head_explorer.remove_file_and_get(out_file_key)
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            candidate_aliases = \
                        self.meta_testcase_tool.get_candidate_tools_aliases(\
                                test_tool_type_list=self.cp_data.test_types)

            all_tests = self.meta_testcase_tool.get_testcase_info_object(\
                                   candidate_tool_aliases=candidate_aliases)\
                                                            .get_tests_list()

            selected_tests = []
            for meta_test in all_tests:
                toolalias, _ = DriversUtils.reverse_meta_element(meta_test)
                if toolalias in candidate_aliases:
                    selected_tests.append(meta_test)

            # TODO: use the actual selector. For now just use all tests

            # Check for flakiness
            logging.debug("# Checking for tests flakiness ...")
            flaky_tests = self.meta_testcase_tool.check_get_flakiness(\
                                                                selected_tests)
            if len(flaky_tests) > 0:
                if self.config.DISCARD_FLAKY_TESTS.get_val():
                    selected_tests = \
                                list(set(selected_tests) - set(flaky_tests))
                else:
                    ERROR_HANDLER.error_exit("There are Flaky tests!!", \
                                                                    __file__)
            else:
                logging.debug("# No Flaky Test :)")

            # write the tests
            common_fs.dumpJSON(list(selected_tests), out_file)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())
            # Destroy meta test checkpointer
            #self.meta_testexec_optimization_tool.get_checkpoint_state_object()\
            #                                            .destroy_checkpoint()
        elif task == checkpoint_tasks.Tasks.PASS_FAIL_TESTS_EXECUTION:
            # Make sure that the Matrices dir exists
            self.head_explorer.get_or_create_and_get_dir(\
                                            outdir_struct.RESULTS_MATRICES_DIR)

            matrix_file_key = outdir_struct.TMP_TEST_PASS_FAIL_MATRIX
            matrix_file = self.head_explorer.get_file_pathname(matrix_file_key)
            execoutput_file_key = \
                                outdir_struct.TMP_PROGRAM_TESTEXECUTION_OUTPUT
            if self.config.GET_PASSFAIL_OUTPUT_SUMMARY.get_val():
                # Make sure that the exec Output dir exists
                self.head_explorer.get_or_create_and_get_dir(\
                            outdir_struct.RESULTS_TESTEXECUTION_OUTPUTS_DIR)

                execoutput_file = self.head_explorer.get_file_pathname(\
                                                           execoutput_file_key)
            else:
                execoutput_file = None
                                    
            # @Checkpointing
            if task_untouched:
                if self.meta_testcase_tool.has_checkpointer():
                    self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

                self.head_explorer.remove_file_and_get(matrix_file_key)
                self.head_explorer.remove_file_and_get(execoutput_file_key)
                self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .restart_task()
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            # Execute tests
            test_list_file = self.head_explorer.get_file_pathname(\
                                        outdir_struct.TMP_SELECTED_TESTS_LIST)

            meta_testcases = common_fs.loadJSON(test_list_file)

            # Check pass fail
            self.meta_testcase_tool.runtests(meta_testcases=meta_testcases, \
                        stop_on_failure=\
                                self.config.STOP_TESTS_EXECUTION_ON_FAILURE\
                                                                .get_val(), \
                        recalculate_execution_times=True, \
                        fault_test_execution_matrix_file=matrix_file, \
                        fault_test_execution_execoutput_file=execoutput_file, \
                        test_prioritization_module=\
                                        self.meta_testexec_optimization_tool, \
                        finish_destroy_checkpointer=False)
            
            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())
            # Destroy meta test checkpointer
            self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

        elif task == checkpoint_tasks.Tasks.CRITERIA_GENERATION_GUIDANCE:
            pass #TODO (Maybe could be used someday. for now, just skip it)
        elif task == checkpoint_tasks.Tasks.CRITERIA_GENERATION:
            # @Checkpointing
            if task_untouched:
                if self.meta_criteria_tool.has_checkpointer():
                    self.meta_criteria_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

                self.meta_criteria_tool.get_checkpoint_state_object()\
                                                        .restart_task()
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            self.meta_criteria_tool.instrument_code(criteria_enabled_list=\
                                    self.config.ENABLED_CRITERIA.get_val(), \
                                    finish_destroy_checkpointer=False)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())
            # Destroy meta test checkpointer
            self.meta_criteria_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()
        elif task == checkpoint_tasks.Tasks.\
                                CRITERIA_EXECUTION_SELECTION_PRIORITIZATION:
            pass #TODO (Maybe could be used someday. for now, just skip it)
            #TODO: make it as a driver that will implement techniques 
            # (per tool if needed)
            out_file_key = outdir_struct.TMP_SELECTED_CRITERIA_OBJECTIVES_LIST
            out_file = self.head_explorer.get_file_pathname(out_file_key)
                                        
            # @Checkpointing
            if task_untouched:
                if self.meta_criteria_tool.has_checkpointer():
                    self.meta_criteria_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()
                self.head_explorer.remove_file_and_get(out_file_key)
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            selected_TO = {crit.get_str(): None \
                            for crit in self.config.ENABLED_CRITERIA.get_val()}
            for crit, sel_tech in \
                        self.config.CRITERIA_ELEM_SELECTIONS.get_val().items():
                info_obj = self.meta_criteria_tool\
                                            .get_criterion_info_object(crit)
                if info_obj is None:
                    continue
                all_to = info_obj.get_elements_list()
                # make selection
                if sel_tech != 'DummyRandom':
                    ERROR_HANDLER.error_exit(\
                        'only random TO selection supported now!', __file__)

                # make DummyRandom selection
                sel_count =  self.config\
                            .MAX_CRITERIA_ELEM_SELECTION_NUM_PERCENT.get_val()
                if type(sel_count) == str:
                    if sel_count.endswith('%'):
                        sel_count = float(sel_count[:-1])
                        ERROR_HANDLER.assert_true(sel_count > 0 \
                                                    and sel_count <= 100, \
                                "invalid selection percentage ({})".format(\
                                                        sel_count), __file__)
                        sel_count = int(math.ceil(\
                                            len(all_to) * sel_count / 100.0))
                    else:
                        ERROR_HANDLER.assert_true(sel_count.isdigit(), \
                            'invalid selection number ({})'.format(sel_count),\
                                                                    __file__)
                        sel_count = int(sel_count)
                else:
                    ERROR_HANDLER.assert_true(type(sel_count) == int, \
                            "invalid selection number ({})".format(sel_count),\
                                                                    __file__)
                ERROR_HANDLER.assert_true(sel_count > 0, \
                                "selection number must be positive", __file__)
                if sel_count >= len(all_to):
                    selected_TO[crit.get_str()] = all_to
                else:
                    selected_TO[crit.get_str()] = random.sample(all_to, \
                                                                    sel_count)
            
            # write down selection
            common_fs.dumpJSON(selected_TO, out_file)

        elif task == checkpoint_tasks.Tasks.CRITERIA_TESTS_EXECUTION:
            # Make sure that the Matrices dir exists
            self.head_explorer.get_or_create_and_get_dir(\
                                            outdir_struct.RESULTS_MATRICES_DIR)

            matrix_files_keys = {}
            matrix_files = {}
            execoutput_files_keys = {}
            execoutput_files = {}
            for criterion in self.config.ENABLED_CRITERIA.get_val():
                matrix_files_keys[criterion] = \
                                outdir_struct.TMP_CRITERIA_MATRIX[criterion]
                matrix_files[criterion] = \
                                self.head_explorer.get_file_pathname(\
                                                matrix_files_keys[criterion])
                execoutput_files_keys[criterion] = \
                        outdir_struct.TMP_CRITERIA_EXECUTION_OUTPUT[criterion]
                if criterion in self.config.CRITERIA_WITH_OUTPUT_SUMMARY\
                                                                    .get_val():
                    # Make sure that the Exec output dir exists
                    self.head_explorer.get_or_create_and_get_dir(\
                            outdir_struct.RESULTS_TESTEXECUTION_OUTPUTS_DIR)

                    execoutput_files[criterion] = \
                                self.head_explorer.get_file_pathname(\
                                            execoutput_files_keys[criterion])
                else:
                    execoutput_files[criterion] = None

            # @Checkpointing
            if task_untouched:
                if self.meta_criteria_tool.has_checkpointer():
                    self.meta_criteria_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

                for _, matrix_file_key in list(matrix_files_keys.items()):
                    self.head_explorer.remove_file_and_get(matrix_file_key)
                for _, execoutput_file_key in list(\
                                                execoutput_files_keys.items()):
                    self.head_explorer.remove_file_and_get(execoutput_file_key)
                self.meta_criteria_tool.get_checkpoint_state_object()\
                                                        .restart_task()
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            # XXX: Criteria element execution selection loading
            crit_TO_list_by_crit = None
            if self.config.ONLY_EXECUTE_SELECTED_CRITERIA_ELEM.get_val():
                criteria_TO_sel_file = self.head_explorer.get_file_pathname(\
                        outdir_struct.TMP_SELECTED_CRITERIA_OBJECTIVES_LIST)
                raw_crit2to_list = common_fs.loadJSON(criteria_TO_sel_file)
                crit_TO_list_by_crit = {}
                for crit in self.config.ENABLED_CRITERIA.get_val():
                    crit_TO_list_by_crit[crit] = \
                                            raw_crit2to_list[crit.get_str()]

            # Get sequence
            criteria_set_sequence = self.config.CRITERIA_SEQUENCE.get_val()
            #if criteria_set_sequence is None:
            #    criteria_set_sequence = criteria_pkg.CRITERIA_SEQUENCE
            for cs_pos, criteria_set in enumerate(criteria_set_sequence):
                criteria_set &= set(matrix_files)
                if len(criteria_set) == 0:
                    continue

                # ensure right criteria
                used_crit_TO_list_by_crit = copy.deepcopy(crit_TO_list_by_crit)
                if used_crit_TO_list_by_crit is not None:
                    todel = set(used_crit_TO_list_by_crit) - criteria_set
                    for td in todel:
                        del used_crit_TO_list_by_crit[td]

                # Was it already checkpointed w.r.t criteria set seq
                if self.cp_data.criteria_set_is_executed(cs_pos, criteria_set):
                    continue
                
                # If we have a new criteria set id
                self.cp_data.switchto_new_criteria_set(cs_pos, criteria_set)

                # get matrices by criteria
                test_list_file = self.head_explorer.get_file_pathname(\
                                        outdir_struct.TMP_SELECTED_TESTS_LIST)
                meta_testcases = common_fs.loadJSON(test_list_file)
                
                criterion_to_matrix = {\
                                    c: matrix_files[c] for c in criteria_set}

                # TODO: check set based on the criteria for which execout is enabled
                criterion_to_execoutput = {\
                                c: execoutput_files[c] for c in criteria_set}

                # TODO: make recovery mechanism (like atomic) if execution
                #           is interrupted after the matrix is written 
                #           but before checkpoint
                #       The same goes for after the matrix is written to 
                #       'update_matrix_to_cover_when_difference'

                # XXX execute
                self.meta_criteria_tool.runtests_criteria_coverage( \
                            testcases=meta_testcases, \
                            criterion_to_matrix=criterion_to_matrix, \
                            criterion_to_executionoutput=\
                                                    criterion_to_execoutput, \
                            criteria_element_list_by_criteria=\
                                                    used_crit_TO_list_by_crit,
                            cover_criteria_elements_once=self.config.\
                                    COVER_CRITERIA_ELEMENTS_ONCE.get_val(),\
                            prioritization_module_by_criteria=\
                                    self.meta_criteriaexec_optimization_tools,\
                            finish_destroy_checkpointer=True)

                # Update matrix if needed to have output diff or such
                for crit in criteria_set & set(self.config\
                                .CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM\
                                                                .get_val()):
                    pf_matrix_file = self.head_explorer.get_file_pathname(\
                                    outdir_struct.TMP_TEST_PASS_FAIL_MATRIX)
                    if not os.path.isfile(pf_matrix_file):
                        #In case already did stats
                        pf_matrix_file = self.head_explorer.get_file_pathname(\
                                    outdir_struct.TEST_PASS_FAIL_MATRIX)
                    if self.config.GET_PASSFAIL_OUTPUT_SUMMARY.get_val():
                        pf_execoutput_file = \
                                        self.head_explorer.get_file_pathname(\
                                outdir_struct.TMP_PROGRAM_TESTEXECUTION_OUTPUT)
                        if not os.path.isfile(pf_execoutput_file):
                            pf_execoutput_file = \
                                        self.head_explorer.get_file_pathname(\
                                outdir_struct.PROGRAM_TESTEXECUTION_OUTPUT)
                    else:
                        pf_execoutput_file = None
                    DriversUtils.update_matrix_to_cover_when_difference(\
                                                criterion_to_matrix[crit], \
                                            criterion_to_execoutput[crit], \
                                            pf_matrix_file, pf_execoutput_file)

                # @Checkpointing
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

        elif task == checkpoint_tasks.Tasks.PASS_FAIL_STATS:
            # Make sure that the Matrices dir exists
            self.head_explorer.get_or_create_and_get_dir(\
                                            outdir_struct.RESULTS_STATS_DIR)

            tmp_matrix_file = self.head_explorer.get_file_pathname(\
                                    outdir_struct.TMP_TEST_PASS_FAIL_MATRIX)
            matrix_file = self.head_explorer.get_file_pathname(\
                                    outdir_struct.TEST_PASS_FAIL_MATRIX)
            tmp_execoutput_file = self.head_explorer.get_file_pathname(\
                                outdir_struct.TMP_PROGRAM_TESTEXECUTION_OUTPUT)
            execoutput_file = self.head_explorer.get_file_pathname(\
                                    outdir_struct.PROGRAM_TESTEXECUTION_OUTPUT)
            # Merge TMP pass fail and potentially existing pass fail
            StatsComputer.merge_lmatrix_into_right(\
                                                tmp_matrix_file, matrix_file)
            if self.config.GET_PASSFAIL_OUTPUT_SUMMARY.get_val():
                StatsComputer.merge_lexecoutput_into_right(\
                                        tmp_execoutput_file, execoutput_file)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            # Cleanup
            self.head_explorer.remove_file_and_get(\
                                    outdir_struct.TMP_TEST_PASS_FAIL_MATRIX)
            if self.config.GET_PASSFAIL_OUTPUT_SUMMARY.get_val():
                self.head_explorer.remove_file_and_get(\
                                outdir_struct.TMP_PROGRAM_TESTEXECUTION_OUTPUT)

        elif task == checkpoint_tasks.Tasks.CRITERIA_STATS:
            # Make sure that the Matrices dir exists
            self.head_explorer.get_or_create_and_get_dir(\
                                            outdir_struct.RESULTS_STATS_DIR)

            # Merge TMP criteria and potentially existing criteria
            for criterion in self.config.ENABLED_CRITERIA.get_val():
                tmp_matrix_file = self.head_explorer.get_file_pathname(\
                                outdir_struct.TMP_CRITERIA_MATRIX[criterion])
                matrix_file = self.head_explorer.get_file_pathname(\
                                outdir_struct.CRITERIA_MATRIX[criterion])
                tmp_execoutput_file = self.head_explorer.get_file_pathname(\
                        outdir_struct.TMP_CRITERIA_EXECUTION_OUTPUT[criterion])
                execoutput_file = self.head_explorer.get_file_pathname(\
                            outdir_struct.CRITERIA_EXECUTION_OUTPUT[criterion])
                StatsComputer.merge_lmatrix_into_right(tmp_matrix_file, \
                                                                matrix_file)
                if criterion in self.config.CRITERIA_WITH_OUTPUT_SUMMARY\
                                                                    .get_val():
                    StatsComputer.merge_lexecoutput_into_right(\
                                        tmp_execoutput_file, execoutput_file)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj())

            # Cleanup
            for criterion in self.config.ENABLED_CRITERIA.get_val():
                self.head_explorer.remove_file_and_get(\
                                outdir_struct.TMP_CRITERIA_MATRIX[criterion])

        elif task == checkpoint_tasks.Tasks.AGGREGATED_STATS:
            # Get the test list and criteria element list
            self.meta_testcase_tool.get_testcase_info_file()
            for criterion in self.config.ENABLED_CRITERIA.get_val():
                self.meta_criteria_tool.get_criterion_info_file(criterion)

            # Other results
            other_res = self.head_explorer.get_or_create_and_get_dir(\
                                            outdir_struct.OTHER_COPIED_RESULTS)
            flake_dir = self.meta_testcase_tool.get_flakiness_workdir()
            if os.path.isdir(flake_dir):
                shutil.copytree(flake_dir, os.path.join(other_res, \
                                                os.path.basename(flake_dir)))

            # Compute the final stats (MS, ...)
            StatsComputer.compute_stats(self.config, self.head_explorer, \
                                                            self.checkpointer)
        #-------------------------------------------------------------------

        if not self.cp_data.tasks_obj.task_is_complete(task):
            # @Checkpoint: set task as done
            self.cp_data.tasks_obj.set_task_completed(task)

            # @Checkpoint: write checkpoint
            self.checkpointer.write_checkpoint(\
                                        json_obj=self.cp_data.get_json_obj())
    #~ def _execute_task()

    @classmethod
    def create_repo_manager(cls, config):
        repo_mgr = RepositoryManager(\
                    repository_rootdir=config.REPOSITORY_ROOT_DIR.get_val(),\
                    repo_executables_relpaths=\
                            config.REPO_EXECUTABLE_RELATIVE_PATHS.get_val(),\
                    dev_test_runner_func=\
                            config.CUSTOM_DEV_TEST_RUNNER_FUNCTION.get_val(),\
                    dev_test_program_wrapper=\
                            config.CUSTOM_DEV_TEST_PROGRAM_WRAPPER_CLASS.\
                                                                    get_val(),\
                    code_builder_func=config.CODE_BUILDER_FUNCTION.get_val(),\
                    source_files_to_objects=\
                        config.TARGET_SOURCE_INTERMEDIATE_CODE_MAP.get_val(),\
                    dev_tests_list=config.DEVELOPER_TESTS_LIST.get_val(),\
                    )
        return repo_mgr
    #~ def create_repo_manager()

    def _create_meta_test_tool(self, config, head_explorer):
        # create and return the metatest_tool
        meta_test_tool = MetaTestcaseTool(\
                        language=config.PROGRAMMING_LANGUAGE.get_val(),\
                        tests_working_dir=self.head_explorer.get_dir_pathname(\
                                            outdir_struct.TESTSCASES_WORKDIR),\
                        code_builds_factory=self.cb_factory,
                        test_tool_config_list=\
                                    config.TESTCASE_TOOLS_CONFIGS.get_val(),\
                        head_explorer=head_explorer)
        return meta_test_tool
    #~ def _create_meta_test_tool()

    def _create_meta_criteria_tool(self, config, testcase_tool):
        meta_criteria_tool = MetaCriteriaTool(\
                    language=config.PROGRAMMING_LANGUAGE.get_val(),\
                    meta_test_generation_obj=testcase_tool,\
                    criteria_working_dir=\
                                        self.head_explorer.get_dir_pathname(\
                                            outdir_struct.CRITERIA_WORKDIR),\
                    code_builds_factory=self.cb_factory,
                    tools_config_by_criterion_dict=\
                        config.CRITERIA_TOOLS_CONFIGS_BY_CRITERIA.get_val(),)
        return meta_criteria_tool
    #~ def _create_meta_criteria_tool()

    def _create_meta_testgen_guidance(self, config):
        # TODO
        #ERROR_HANDLER.error_exit("To be implemented", __file__)
        tgg_tool = None
        return tgg_tool
    #~ def _create_meta_testgen_guidance()

    def _create_meta_testexec_optimization(self, config):
        # TODO
        #ERROR_HANDLER.error_exit("To be implemented", __file__)
        teo_tool = None
        return teo_tool
    #~ def _create_meta_testexec_optimization()

    def _create_meta_criteriagen_guidance(self, config):
        # TODO
        #ERROR_HANDLER.error_exit("To be implemented", __file__)
        cgg_tool = None
        return cgg_tool
    #~ def _create_meta_criteriagen_guidance()

    def _create_meta_criteriaexec_optimization(self, config):
        ceo_tools = None
        if len(config.CRITERIA_EXECUTION_OPTIMIZERS.get_val()) > 0:
            ceo_tools = {}
            for crit, opt in \
                        config.CRITERIA_EXECUTION_OPTIMIZERS.get_val().items():
                ceo_tools[crit] = opt.get_optimizer()\
                                            (config, self.head_explorer, crit) 
        return ceo_tools
    #~ def _create_meta_criteriaexec_optimization()

    def _initialize_output_structure(self, cleanstart=False):
        if cleanstart:
            if common_mix.confirm_execution(
                                    "Do you really want to clean the outdir?"):
                self.head_explorer.clean_create_and_get_dir(\
                                            outdir_struct.TOP_OUTPUT_DIR_KEY)
            else:
                ERROR_HANDLER.error_exit("Cancelled Cleanstart!", __file__)
        else:
            self.head_explorer.get_or_create_and_get_dir(\
                                            outdir_struct.TOP_OUTPUT_DIR_KEY)

        for folder in [outdir_struct.CONTROLLER_DATA_DIR, \
                                    outdir_struct.CTRL_CHECKPOINT_DIR, \
                                    outdir_struct.CTRL_LOGS_DIR, \
                                    outdir_struct.EXECUTION_TMP_DIR]:
            self.head_explorer.get_or_create_and_get_dir(folder)
    #~ def _initialize_output_structure()

    def _get_checkpoint_files(self):
        cp_file = self.head_explorer.get_file_pathname(\
                                        outdir_struct.EXECUTION_STATE)
        cp_file_bak = self.head_explorer.get_file_pathname(\
                                        outdir_struct.EXECUTION_STATE_BAKUP)
        return (cp_file, cp_file_bak)
    #~ def _get_checkpoint_files()
#~ class Executor
