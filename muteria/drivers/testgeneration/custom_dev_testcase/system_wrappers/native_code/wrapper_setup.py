
from __future__ import print_function

from muteria.drivers.testgeneration.custom_dev_testcase.system_wrappers.\
                                    base_wrapper_setup import BaseSystemWrapper

class SystemWrapper(BaseSystemWrapper):

    wrapper_template_filename = "MUTERIA_WRAPPER.sh.in"
    wrapper_template_string = None
    dev_null = "/dev/null"

#~ class SystemWrapper