
from __future__ import print_function

import abc

class TestcaseFormatsCodes(dict):
    """ Set each field to the corresponding test class or None if no class
        is implemented.
    """

    KTEST_V1 = None
    KTEST_V2 = None
    GOOGLE_TESTS = None
    JUNIT_TESTS = None

    @classmethod
    def is_testcase_format_class(cls, testcase_format):
        return testcase_format is not None 
    #~ def is_testcase_format_class()
#~ class TestcaseFormatsCodes

class BaseTestcaseFormat(abc.ABC):
    @abc.abstractmethod
    def get_test_suffixes(self):
        """ Return the test files suffixes
        """
        pass
    #~ def get_test_suffixes()

    @abc.abstractmethod
    def test_duplicates(self, test_filename_suffixes, dir_list, file_list):
        """Find duplicate test in given dir_list (having suffix from 
            test_filename_suffixes, Non recursively) and files in file_list
            :return: list of dupliate elements (each duplicate element 
                    is a list of testcases that are duplicate between
                    each others)
        """
        pass
    #~ def test_duplicates()

    @abc.abstractmethod
    def get_supported_convert_into(self):
        pass
    #~ def get_supported_convert_into()

    @abc.abstractmethod
    def convert_into(self, dest_type, src_testfile, dest_testfile):
        """ Convert src_testfile of this type into dest_testfile of dest_type
        """
        pass
    #~ def convert_into()

    @abc.abstractmethod
    def get_supported_convert_from(self):
        pass
    #~ def get_supported_convert_from()

    @abc.abstractmethod
    def convert_from(self, src_type, src_testfile, dest_testfile):
        """ Convert src_testfile of src_type into dest_testfile of this type
        """
        pass
    #~ def convert_from()
#~ class BaseTestcaseFormat()