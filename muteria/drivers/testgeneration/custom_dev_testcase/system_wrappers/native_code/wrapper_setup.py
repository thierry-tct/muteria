
from __future__ import print_function

import os

from muteria.drivers.testgeneration.custom_dev_testcase.system_wrappers.\
                                base_wrapper_setup import BaseSystemWrapper, \
                                                BaseSystemTestSplittingWrapper

class SystemTestSplittingWrapper(BaseSystemTestSplittingWrapper):
    def set_wrapper(self, workdir, exe_path_map):
        """ Return the new exe path map
        """
        print ("Implement!!!")
    #~ def set_wrapper()

    def switch_to_new_test(self, workdir):
        """ reset the counters
        """
        print ("Implement!!!")
    #~ def switch_to_new_test()

    def collect_data(self, workdir):
        """ get number of sub tests and args
        """
        print ("Implement!!!")
    #~ def collect_data()
#~ class SystemTestSplittingWrapper

class SystemWrapper(BaseSystemWrapper):

    wrapper_template_filename = "MUTERIA_WRAPPER.sh.in"

    def get_dev_null(self):
        return "/dev/null"
    #~ def get_dev_null()

    def _get_wrapper_template_string(self):
        wrapper_template_file = os.path.join(os.path.dirname(__file__), \
                                                self.wrapper_template_filename)
        with open(wrapper_template_file) as template:
            return template.read()
    #~ def _get_wrapper_template_string()

    def _get_timedout_codes(self):
        # Timeout codes for GNU timeout
        return (124, 137)
    #~ def _get_timedout_codes()

    def get_test_splitting_wrapper_class(self):
        return SystemTestSplittingWrapper
    #~ def get_sub_test_id_env_vars()
#~ class SystemWrapper