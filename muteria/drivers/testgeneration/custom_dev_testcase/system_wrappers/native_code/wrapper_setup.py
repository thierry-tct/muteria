
from __future__ import print_function

import os

from muteria.drivers.testgeneration.custom_dev_testcase.system_wrappers.\
                                    base_wrapper_setup import BaseSystemWrapper

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
#~ class SystemWrapper