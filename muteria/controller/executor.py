"""
TODO: Add support for multi versions of results 
"""

from __future__ import print_function

import os 
import logging
import shutil
import glob

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

from muteria.repositoryandcode.repository_manager import RepositoryManager
from muteria.repositoryandcode.code_builds_factory import CodeBuildsFactory

from muteria.drivers.testgeneration.meta_testcasetool import MetaTestcaseTool
from muteria.drivers.criteria.meta_testcriteriatool import MetaCriteriaTool

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
        return retval
    #~ def get_json_obj()

    def update_from_json_obj(self, json_obj):
        self.update_all(**json_obj)
        self.tasks_obj = checkpoint_tasks.TaskOrderingDependency(\
                                                    json_obj=self.tasks_obj)
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
        if self.criteria_set_pos > seq_id:
            return True
        if self.criteria_set_pos == seq_id and \
                                set(self.criteria_set) != set(criteria_set):
            ERROR_HANDLER.error_exit("cp criteria_set changed", __file__)
        return False
    #~ def criteria_set_is_executed()

    def switchto_new_criteria_set(self, seq_id, criteria_set):
        if seq_id > self.criteria_set_pos:
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
    def __init__(self, config, top_timeline_explorer):
        self.config = config
        self.top_timeline_explorer = top_timeline_explorer

        self.head_explorer = self.top_timeline_explorer.get_latest_explorer()
        self._initialize_output_structure(cleanstart=\
                                self.config.EXECUTION_CLEANSTART._get_val())
        if not logging_setup.is_setup():
            logging_setup.setup(logfile=self.head_explorer.get_file_pathname(\
                                                outdir_struct.MAIN_LOG_FILE))
        # Create repo manager
        # XXX The repo manager automatically revert any previous problem
        self.repo_mgr = Executor.create_repo_manager(config)

        # set error handlers for revert repo
        common_mix.ErrorHandler.set_corresponding_repos_manager(self.repo_mgr)

        # create codes builders
        self.cb_factory = CodeBuildsFactory(self.repo_mgr)
    #~ def __init__()

    def main(self):
        """ Executor entry point
        """
        # Initialize output structure
        self._initialize_output_structure(cleanstart=self.config.CLEANSTART)

        # Make checkpointer
        self.checkpointer = \
                    common_fs.CheckpointState(*self._get_checkpoint_files())
        if self.checkpointer.is_finished():
            return

        # Meta testcases tool
        self.meta_testcase_tool = self._create_meta_test_tool(self.config)

        # Meta criteria
        self.meta_criteria_tool = self._create_meta_criteria_tool(self.config)

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
        self.meta_criteriaexec_optimization_tool = \
                    self._create_meta_criteriaexec_optimization(self.config)


        # See whether starting or continuing
        check_pt_obj = self.checkpointer.load_checkpoint_or_start(\
                                            ret_detailed_exectime_obj=False)
        
        test_tool_type_sequence = self.config.TEST_TOOL_TYPE_SEQUENCE.get_val()

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

        task_set = None
        # by testtool type sequence loop
        for seq_id, test_tool_types in enumerate(test_tool_type_sequence):
            
            # Was it already checkpointed w.r.t test type seq
            if self.cp_data.test_tool_types_is_executed(\
                                                    seq_id, test_tool_types):
                continue
            
            # If we have a new seq_id, it is another test type loop
            self.cp_data.switchto_new_test_tool_types(seq_id, test_tool_types)

            # Actual Execution in the temporary dir (until before finish)
            while True:
                # 1. get executing task
                task_set = self.cp_data.tasks_obj.get_next_todo_tasks()

                # stop if the next task is FINISHED
                if len(task_set) == 0 or (len(task_set) == 1 and \
                        list(task_set)[0] == checkpoint_tasks.Tasks.FINISHED):
                    break

                # 2. execute the tasks
                # (TODO: parallelism)
                for task in task_set:
                    self._execute_task(task)

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
                self.meta_testcase_tool.clear_working_dir() 
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj)

            # Generate the tests
            self.meta_testcase_tool.generate_tests(\
                                test_tool_type_list=self.cp_data.test_types)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj)
            # Destroy meta test checkpointer
            self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

        elif task == checkpoint_tasks.Tasks.\
                                    TESTS_EXECUTION_SELECTION_PRIORITIZATION:
            out_file = self.head_explorer.get_file_pathname(\
                                        outdir_struct.TMP_SELECTED_TESTS_LIST)
            # @Checkpointing
            if task_untouched:
                self.head_explorer.remove_file_and_get(out_file)
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj)

            # TODO: use the actual selector. For now just use all tests
            selected_tests = self.meta_testcase_tool.\
                                    get_testcase_info_object().get_tests_list()
            common_fs.dumpJSON(selected_tests, out_file)

            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj)
            # Destroy meta test checkpointer
            #self.meta_testexec_optimization_tool.get_checkpoint_state_object()\
            #                                            .destroy_checkpoint()
        elif task == checkpoint_tasks.Tasks.PASS_FAIL_TESTS_EXECUTION:
            matrix_file = self.head_explorer.get_path_filename(\
                                    outdir_struct.TMP_TEST_PASS_FAIL_MATRIX)
            # @Checkpointing
            if task_untouched:
                self.head_explorer.remove_file_and_get(matrix_file)
                self.cp_data.tasks_obj.set_task_executing(task)
                self.checkpointer.write_checkpoint(self.cp_data.get_json_obj)

            # Execute tests
            test_list_file = self.head_explorer.get_file_pathname(\
                                        outdir_struct.TMP_SELECTED_TESTS_LIST)
            meta_testcases = common_fs.loadJSON(test_list_file)
            self.meta_testcase_tool.runtests(meta_testcases=meta_testcases, \
                        stop_on_failure=self.config.STOP_ON_TEST_FAILURE, \
                        fault_test_execution_matrix_file=matrix_file, \
                        test_prioritization_module=\
                                        self.meta_testexec_optimization_tool)


            # @Checkpointing
            self.cp_data.tasks_obj.set_task_completed(task)
            self.checkpointer.write_checkpoint(self.cp_data.get_json_obj)
            # Destroy meta test checkpointer
            self.meta_testcase_tool.get_checkpoint_state_object()\
                                                        .destroy_checkpoint()

        elif task == checkpoint_tasks.Tasks.CRITERIA_GENERATION_GUIDANCE:
            pass #TODO (Maybe could be used someday. for now, just skip it)
        elif task == checkpoint_tasks.Tasks.CRITERIA_GENERATION:
            pass #TODO
        elif task == checkpoint_tasks.Tasks.\
                            CRITERIA_EXECUTION_SELECTION_PRIORITIZATION:
            pass #TODO
        elif task == checkpoint_tasks.Tasks.CRITERIA_TESTS_EXECUTION:
            criteria_set_sequence = self.config.CRITERIA_SEQUENCE.get_val()
            for cs_pos, criteria_set in enumerate(criteria_set_sequence):
                pass #TODO

        elif task == checkpoint_tasks.Tasks.PASS_FAIL_STATS:
            pass #TODO
        elif task == checkpoint_tasks.Tasks.CRITERIA_STATS:
            pass #TODO
        elif task == checkpoint_tasks.Tasks.AGGREGATED_STATS:
            pass #TODO
        #-------------------------------------------------------------------

        if not self.cp_data.tasks_obj.task_is_complete(task):
            # @Checkpoint: set task as done
            self.cp_data.tasks_obj.set_task_completed(task)

            # @Checkpoint: write checkpoint
            self.checkpointer.write_checkpoint(\
                                        json_obj=self.cp_data.get_json_obj())

        # TODO: merge the results into previous ones (if applicable)
    #~ def _execute_task()

    @classmethod
    def create_repo_manager(cls, config):
        repo_mgr = RepositoryManager(\
                    repository_rootdir=config.REPOSITORY_ROOT_DIR.get_val(),\
                    repo_executable_relpath=\
                            config.REPO_EXECUTABLE_RELATIVE_PATH.get_val(),\
                    dev_test_runner_func=\
                            config.CUSTOM_DEV_TEST_RUNNER_FUNCTION.get_val(),\
                    code_builder_func=config.CODE_BUILD_FUNCTION.get_val(),\
                    source_files_list=\
                                config.TARGET_SOURCE_FILES_LIST.get_val(),\
                    dev_tests_list=config.DEVELOPER_TESTS_LIST.get_val(),\
                    )
        return repo_mgr
    #~ def create_repo_manager()

    def _create_meta_test_tool(self, config):
        # create and return the metatest_tool
        meta_test_tool = MetaTestcaseTool(\
                        language=config.PROGRAMMING_LANGUAGE.get_val(),\
                        tests_working_dir=self.head_explorer.get_dir_pathname(\
                                            outdir_struct.TESTSCASES_WORKDIR),\
                        code_builds_factory=self.cb_factory,
                        test_tool_config_list=config.TESTCASE_TOOLS_CONFIGS,)
        return meta_test_tool
    #~ def _create_meta_test_tool()

    def _create_meta_criteria_tool(self, config):
        meta_criteria_tool = MetaCriteriaTool(\
                        language=config.PROGRAMMING_LANGUAGE.get_val(),\
                        criteria_working_dir=\
                                        self.head_explorer.get_dir_pathname(\
                                            outdir_struct.CRITERIA_WORKDIR),\
                        code_builds_factory=self.cb_factory,
                        tool_config_list_by_criteria=\
                                    config.CRITERIA_TOOLS_CONFIGS_BY_CRITERIA,)
        return meta_criteria_tool
    #~ def _create_meta_criteria_tool()

    def _create_meta_testgen_guidance(self, config):
        # TODO
        ERROR_HANDLER.error_exit("To be implemented", __file__)
        tgg_tool = None
        return tgg_tool
    #~ def _create_meta_testgen_guidance()

    def _create_meta_testexec_optimization(self, config):
        # TODO
        ERROR_HANDLER.error_exit("To be implemented", __file__)
        teo_tool = None
        return teo_tool
    #~ def _create_meta_testexec_optimization()

    def _create_meta_criteriagen_guidance(self, config):
        # TODO
        ERROR_HANDLER.error_exit("To be implemented", __file__)
        cgg_tool = None
        return cgg_tool
    #~ def _create_meta_criteriagen_guidance()

    def _create_meta_criteriaexec_optimization(self, config):
        # TODO
        ERROR_HANDLER.error_exit("To be implemented", __file__)
        ceo_tool = None
        return ceo_tool
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