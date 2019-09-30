
from __future__ import print_function

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class TestcasesInfoObject(object):
    """ This class represent the test case informations data structure
    """
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

    def add_test (self, test_name, **kwargs):
        ERROR_HANDLER.assert_true(not self.has_test(test_name), \
                            "Test is already present in this: {}".format(\
                                                    test_name), __file__)
        self.data[self.DATA_KEY][test_name] = kwargs
    #~def add_test ()

    def has_test(self, test_name):
        return test_name in self.data[self.DATA_KEY]
    #~ def has_test():

    def get_tests_list(self):
        return list(self.data[self.DATA_KEY].keys())
    #~ def get_tests_list()

    def update_using(self, toolname, old2new_tests, old_test_info_obj):
        # Update tests
        for old_test_name, new_test_name in list(old2new_tests.items()):
            ERROR_HANDLER.assert_true(\
                        old_test_info_obj.has_test(old_test_name), \
                        "Test not present in old_test_info_obj: {}".format(\
                                                    old_test_name), __file__)
            
            ERROR_HANDLER.assert_true(not self.has_test(new_test_name), \
                            "Test is already present in this: {}".format(\
                                                    new_test_name), __file__)
            self.data[self.DATA_KEY][new_test_name] = \
                        old_test_info_obj.data[self.DATA_KEY][old_test_name]

        # Update Summary
        if self.data[self.SUMMARY_KEY] is None:
            self.data[self.SUMMARY_KEY] = {}
        self.data[self.SUMMARY_KEY][toolname] = \
                        old_test_info_obj.data[self.SUMMARY_KEY]

        # Update Custom
        if self.data[self.CUSTOM_KEY] is None:
            self.data[self.CUSTOM_KEY] = {}
        self.data[self.CUSTOM_KEY][toolname] = \
                        old_test_info_obj.data[self.CUSTOM_KEY]
    #~ def update_using()

    def remove_test(self, test_name):
        ERROR_HANDLER.assert_true(self.has_test(test_name), \
                        "Removing an unexisting test: {}".format(test_name), \
                                                                    __file__)
        del self.data[self.DATA_KEY][test_name]
    #~ def remove_test()

    def get_summary(self):
        return self.data[self.SUMMARY_KEY]
    #~ def get_summary():

    def get_custom(self):
        return self.data[self.CUSTOM_KEY]
    #~ def get_custom():
#~ class TestcasesInfoObject