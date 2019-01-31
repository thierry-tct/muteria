#
#

from __future__ import print_function

import os
import sys
import time
import shutil
import logging
import inspect

import muteria.common.fs as common_fs
#import muteria.common.reposutils as common_reposutils


def confirm_execution(question):
    """
    Ask user to enter Y or N (case-insensitive).

    :return: True if the answer is Y.
    :rtype: bool
    """
    reading_func = input
    if sys.version_info.major < 3:
        reading_func = raw_input
    answer = ""
    while answer not in ["y", "n"]:
        answer = reading_func("%s %s" % (question, "[Y/N] ")).lower()
    return answer == "y"
#~ def confirm_execution()

class ErrorHandler(object):
    def __init__(self):
        pass

    def error_exit(self, error_code=1, err_string=None, ask_revert=True):
        logging.error("# Error happened in function %s" % inspect.stack()[1][3])
        if err_string:
            logging.error(err_string)
        if ask_revert and \
                confirm_execution("Do you want to revert repository files?"):
            logging.info("Reverting repository files")
            # TODO implement revert
        print("# Exiting with code %d" % error_code)
        exit(error_code)

    def error_exit_file(file_called_from, error_code=1, \
                                    err_string=None, ask_revert=True):
        '''
        Call this function with the parameter __file__
        '''
        logging.error("# Error happened in file %s" % file_called_from)
        self.error_exit(error_code=error_code, err_string=err_string, \
                                                    ask_revert=ask_revert)
#~ class ErrorHandler

ERROR_HANDLER = ErrorHandler()

class CheckpointState(object):
    EXEC_COMPLETED = "CHECK_POINTED_TASK_COMPLETED"
    EXEC_STARTING = "CHECK_POINTED_TASK_STARTING"
    AGG_TIME_KEY = "AGGREGATED_TIME"
    DETAILED_TIME_KEY = "DETAILED_TIME"
    CHECKPOINT_DATA_KEY = "CHECKPOINT_DATA"

    '''
    '''
    def __init__(self, store_filepath, backup_filepath):
        self.store_filepath = store_filepath
        self.backup_filepath = backup_filepath
        # make sure that sub task are destroyed, restarted
        # when parent is. (Not necessary for finished)
        self.dep_checkpoint_states = set()
        self.started = False
        self.finished = False
        self.starttime = None
        self.aggregated_time = None

        raw_obj = self._get_from_file()
        self._update_this_object(raw_obj)
    #~ def __init__()

    def add_dep_checkpoint_state(self, dep_cp):
        self.dep_checkpoint_states.add(dep_cp)

    def destroy_checkpoint(self):
        for dep_cp in self.dep_checkpoint_states:
            dep_cp.destroy_checkpoint()
        if os.path.isfile(self.backup_filepath):
            os.remove(self.store_filepath)
        if os.path.isfile(self.store_filepath):
            #shutil.copy2(self.store_filepath, self.backup_filepath)
            os.remove(self.store_filepath)
        self.started = False
        self.finished = False
        self.starttime = None
        self.aggregated_time = None
    #~ def destroy_checkpoint()

    def set_finished(self, detailed_exectime_obj=None):
        if not self.started:
            logging.error("%s" % \
                            "finishing checkpointed task while not started")
            ERROR_HANDLER.error_exit()
        self.started = False
        self.finished = True
        self.write_checkpoint(self.EXEC_COMPLETED, \
                                detailed_exectime_obj=detailed_exectime_obj)
        # put last because used in write_checkpoint
        self.starttime = None 
    #~ def set_finished()

    def is_destroyed(self):
        no_files = True
        for dep_cp in self.dep_checkpoint_states:
            no_files &= dep_cp.is_destroyed()
        no_files &= not os.path.isfile(self.store_filepath) and \
                    not os.path.isfile(self.backup_filepath)
        return no_files
    #~ def is_destroyed()

    def is_finished(self):
        return self.finished
    #~ def is_finished()

    def restart_task(self):
        for dep_cp in self.dep_checkpoint_states:
            dep_cp.restart_task()
        self.started = True
        self.finished = False
        self.aggregated_time = 0.0
        self.starttime = time.time()
        self.write_checkpoint(self.EXEC_STARTING)
    #~ def restart_task()

    def load_checkpoint_or_start(self, ret_detailed_exectime_obj=False):
        '''
        This function also show a fresh starting of the execution
        Return None as checkpoint data if start (was not yet started)
                If ret_detailed_exectime_obj is enable, return 
                detailed_exectime_obj as second returned value
        '''
        raw_obj = self._get_from_file()
        # case of resume execution
        if self.starttime is None:
            self.starttime = time.time()
        if raw_obj is None:
            self.restart_task()
        res = raw_obj[self.CHECKPOINT_DATA_KEY]
        if res in [self.EXEC_STARTING, self.EXEC_COMPLETED]:
            res = None
        if ret_detailed_exectime_obj:
            res = (res, raw_obj[self.DETAILED_TIME_KEY])
        return res 
    #~ def load_checkpoint_or_start()

    def write_checkpoint(self, json_obj, detailed_exectime_obj=None):
        remove_back = False
        if os.path.isfile(self.store_filepath):
            shutil.copy2(self.store_filepath, self.backup_filepath)
        else:
            remove_back = True
        raw_obj = { \
                    self.AGG_TIME_KEY: self.aggregated_time, \
                    self.DETAILED_TIME_KEY: detailed_exectime_obj, \
                    self.CHECKPOINT_DATA_KEY: json_obj, \
        }
        common_fs.dumpJSON(raw_obj, self.store_filepath, pretty=True)
        if remove_back:
            os.remove(self.backup_filepath)
    #~ def write_checkpoint()

    def get_execution_time(self):
        if self.starttime is None:
            return self.aggregated_time
        return self.aggregated_time + (time.time() - self.starttime)
    #~ def get_execution_time()

    def get_detailed_execution_time(self):
        raw_obj = self._get_from_file()
        return raw_obj[self.DETAILED_TIME_KEY]
    #~ def get_detailed_execution_time()

    def _get_from_file(self):
        contain = None
        trybackup = True
        if os.path.isfile(self.store_filepath):
            try:
                contain = common_fs.loadJSON(self.store_filepath)
                trybackup = False
            except ValueError:
                trybackup = True
        if trybackup and os.path.isfile(self.backup_filepath):
            try:
                contain = common_fs.loadJSON(self.backup_filepath)
            except ValueError:
                logging.error("%s %s" % ("Both Checkpoint store_file and", \
                                        "backup file are invalid"))
                ERROR_HANDLER.error_exit()
            if not confirm_execution("%s %s" % ("Checkpoint store_file is", \
                    "invalid but backup is valid. Do you want to use backup?")):
                logging.error("%s %s" % ("Execution terminated due to", \
                                            "invalid Checkpoint store_file"))
                ERROR_HANDLER.error_exit()
        
        # Check consistency or update obj
        if contain is not None:
            for key in [self.DETAILED_TIME_KEY, self.AGG_TIME_KEY, \
                                                    self.CHECKPOINT_DATA_KEY]:
                if key not in contain:
                    file_used = self.backup_filepath if trybackup \
                                                    else self.store_filepath
                    logging.error("%s (%s). %s %s" % \
                                ("Invalid checkpoint file", file_used, \
                                    "do not contain the data for", key))
                    ERROR_HANDLER.error_exit()
        return contain
    #~ def _get_from_file()

    def _update_this_object(self, raw_obj):
        if raw_obj is None:
            self.started = False
            self.finished = False
            self.starttime = None
            self.aggregated_time = 0.0
        else:
            agg_time = raw_obj[self.AGG_TIME_KEY]
            checkpoint_data = raw_obj[self.CHECKPOINT_DATA_KEY]
            if checkpoint_data == self.EXEC_STARTING:
                self.started = True
                self.finished = False
            elif checkpoint_data == self.EXEC_COMPLETED:
                self.started = False
                self.finished = True
            self.aggregated_time = float(agg_time)
    #~ def _update_this_object() 
#~ class CheckpointState
