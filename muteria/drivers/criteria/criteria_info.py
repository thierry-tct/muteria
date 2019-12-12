"""
 TODO: fully implement this
"""
from __future__ import print_function

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

from muteria.drivers.criteria import TestCriteria

ERROR_HANDLER = common_mix.ErrorHandler

class CriterionElementInfoObject(object):
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

    def add_element (self, element_name, **kwargs):
        ERROR_HANDLER.assert_true(not self.has_element(element_name), \
                            "Test is already present in this: {}".format(\
                                                    element_name), __file__)
        self.data[self.DATA_KEY][element_name] = kwargs
    #~def add_element ():

    def get_element_data(self, element_name):
        ERROR_HANDLER.assert_true(self.has_element(element_name), \
                            "Test is not present in this: {}".format(\
                                                    element_name), __file__)
        return self.data[self.DATA_KEY][element_name]
    #~ def get_element_data()

    def has_element(self, element_name):
        return element_name in self.data[self.DATA_KEY]
    #~ def has_element():

    def get_elements_list(self):
        return list(self.data[self.DATA_KEY].keys())
    #~ def get_elements_list()

    def update_using(self, toolname, old2new_elements, old_element_info_obj):
        # Update elements
        for old_elem_name, new_elem_name in list(old2new_elements.items()):
            ERROR_HANDLER.assert_true(\
                        old_element_info_obj.has_element(old_elem_name), \
                        "TO not present in old_element_info_obj: {}".format(\
                                                    old_elem_name), __file__)
            
            ERROR_HANDLER.assert_true(not self.has_element(new_elem_name), \
                            "TO is already present in this: {}".format(\
                                                    new_elem_name), __file__)
            self.data[self.DATA_KEY][new_elem_name] = \
                        old_element_info_obj.data[self.DATA_KEY][old_elem_name]
        # Update Summary
        if self.data[self.SUMMARY_KEY] is None:
            self.data[self.SUMMARY_KEY] = {}
        self.data[self.SUMMARY_KEY][toolname] = \
                        old_element_info_obj.data[self.SUMMARY_KEY]

        # Update Custom
        if self.data[self.CUSTOM_KEY] is None:
            self.data[self.CUSTOM_KEY] = {}
        self.data[self.CUSTOM_KEY][toolname] = \
                        old_element_info_obj.data[self.CUSTOM_KEY]
    #~ def update_using()

    def remove_element(self, element_name):
        ERROR_HANDLER.assert_true(self.has_element(element_name), \
                    "Removing an unexisting element: {}".format(element_name),\
                                                                    __file__)
        del self.data[self.DATA_KEY][element_name]
    #~ def remove_element()

    def get_summary(self):
        return self.data[self.SUMMARY_KEY]
    #~ def get_summary():

    def get_custom(self):
        return self.data[self.CUSTOM_KEY]
    #~ def get_custom():
#~ class CriterionElementInfoObject(object):

class MutantsInfoObject(CriterionElementInfoObject):
    def __init__(self):
        CriterionElementInfoObject.__init__(self)
    #~ def __init__()

    def add_element (self, element_name, mutant_type=None, 
                        mutant_locs=None, mutant_function_name=None, **kwargs):
        CriterionElementInfoObject.add_element(self, element_name, \
                                    mutant_type=mutant_type, \
                                    mutant_srclocs=mutant_locs, \
                                    mutant_function_name=mutant_function_name,\
                                    **kwargs)
    #~def add_element ():

#~ class MutantsInfoObject(object):

"""
NOTE: For new citeria,
Update this dict with the criterion Info module
"""
CriteriaToInfoObject = {
    TestCriteria.STRONG_MUTATION: MutantsInfoObject,
    TestCriteria.WEAK_MUTATION: MutantsInfoObject,
    TestCriteria.MUTANT_COVERAGE: MutantsInfoObject,
}
