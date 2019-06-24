
import logging

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class CheckPointHandler(object):
    FUNC_NAME_KEY = "method_name"
    TASK_ID_KEY = "task_id"
    TOOLS_KEY = "tools"
    OPT_PAYLOAD_KEY = "optional_payload"
    def __init__(self, used_checkpointer):
        self.used_checkpointer = used_checkpointer
        self.current_data = None
        self.get_current_data()

    def get_current_data(self):
        if self.current_data is None:
            self.current_data = \
                        self.used_checkpointer.load_checkpoint_or_start()
            # verify
            if self.current_data is not None:
                if type(self.current_data) != dict:
                    ERROR_HANDLER.error_exit( \
                        "Invalid checkpoint data. Must be a dict", __file__)
                if set(self.current_data) != {self.FUNC_NAME_KEY, \
                                        self.TASK_ID_KEY, self.TOOLS_KEY, \
                                        self.OPT_PAYLOAD_KEY}:
                    ERROR_HANDLER.error_exit( \
                       "Problem with checkpoint data dict key", __file__)

        return self.current_data

    def is_finished(self):
        return self.used_checkpointer.is_finished()

    def is_to_execute(self, func_name, taskid, tool=None):
        dat = self.get_current_data()
        if dat is None:
            return True
        if func_name != self.current_data[self.FUNC_NAME_KEY]:
            return True
        if taskid >= self.current_data[self.TASK_ID_KEY]:
            if taskid > self.current_data[self.TASK_ID_KEY] or \
                             tool not in self.current_data[self.TOOLS_KEY]:
                return True
        return False

    def do_checkpoint(self, func_name, taskid, tool=None, opt_payload=None):
        if self.current_data is None:
            self.current_data = { \
                self.FUNC_NAME_KEY: None, \
                self.TASK_ID_KEY: -1, \
                self.TOOLS_KEY: [], \
                self.OPT_PAYLOAD_KEY: None
            }
        self.current_data[self.FUNC_NAME_KEY] = func_name
        if self.current_data[self.TASK_ID_KEY] != taskid:
            self.current_data[self.TOOLS_KEY] = []
        self.current_data[self.TASK_ID_KEY] = taskid
        self.current_data[self.TOOLS_KEY].append(tool)
        self.current_data[self.OPT_PAYLOAD_KEY] = opt_payload
        self.used_checkpointer.write_checkpoint(self.current_data)

    def set_finished(self, detailed_exectime_obj):
        self.used_checkpointer.set_finished( \
                                detailed_exectime_obj=detailed_exectime_obj)

    def get_optional_payload(self):
        if self.current_data is None:
            return None
        return self.current_data[self.OPT_PAYLOAD_KEY]

    def restart(self):
        self.used_checkpointer.restart_task()

    def destroy(self):
        self.used_checkpointer.destroy_checkpoint()
#~ class CheckPointHandler

