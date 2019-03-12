"""
 TODO: fully implement this
"""
from __future__ import print_function

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class CodesInfoObject(object):
    DATA_KEY = "DATA"
    SUMMARY_KEY = "SUMMARY"
    CUSTOM_KEY = "CUSTOM"
    def __init__(self):
        self.data = {
            self.DATA_KEY: {},
            self.SUMMARY_KEY: None,
            self.CUSTOM_KEY: None,
        }
    #~ def __init__()

    def load_from_file(self, file_path):
        self.data = common_fs.loadJSON(file_path)
    #~ def load_from_file()

    def write_to_file(self, file_path):
        common_fs.dumpJSON(self.data, file_path, pretty=True)
    #~ def write_to_file()

    def add_mutant (self, mutant_name, **kwargs):
        assert False, "Must Implement"
    #~def add_mutant ():

    def has_mutant(self, mutant_name):
        return mutant_name in self.data[self.DATA_KEY]
    #~ def has_mutant():

    def get_mutants_list(self):
        return self.data[self.DATA_KEY].keys()
    #~ def get_mutants_list()

    def update_using(self, toolname, old2new_mutants, old_mutant_info_obj):
        # Update mutants
        for old_mutant_name, new_mutant_name in list(old2new_mutants.items()):
            ERROR_HANDLER.assert_true(\
                        old_mutant_info_obj.has_mutant(old_mutant_name), \
                        "Test not present in old_mutant_info_obj: {}".format(\
                                                    old_mutant_name), __file__)
            
            ERROR_HANDLER.assert_true(not self.has_mutant(new_mutant_name), \
                            "Test is already present in this: {}".format(\
                                                    new_mutant_name), __file__)
            self.data[self.DATA_KEY][new_mutant_name] = \
                            old_mutant_info_obj[self.DATA_KEY][old_mutant_name]
        # Update Summary
        # TODO

        # Update Custom
        # TODO
    #~ def update_using()

    # TODO: Getter for each mutant's info field

    def remove_mutant(self, mutant_name):
        ERROR_HANDLER.assert_true(self.has_mutant(mutant_name), \
                    "Removing an unexisting mutant: {}".format(mutant_name), \
                                                                    __file__)
        del self.data[self.DATA_KEY][mutant_name]
    #~ def remove_mutant()

    def get_summary(self):
        assert False, "Must Implement"
    #~ def get_summary():

    def get_custom(self):
        assert False, "Must Implement"
    #~ def get_custom():
#~ class CodesInfoObject(object):