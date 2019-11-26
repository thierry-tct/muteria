
from __future__ import print_function

import os

import muteria.common.mix as common_mix

from muteria.drivers.testgeneration.custom_dev_testcase.system_wrappers.\
                                base_wrapper_setup import BaseSystemWrapper, \
                                                BaseSystemTestSplittingWrapper

ERROR_HANDLER = common_mix.ErrorHandler

class SystemTestSplittingWrapper(BaseSystemTestSplittingWrapper):
    def set_wrapper(self, workdir, exe_path_map):
        """ Return the new exe path map
        """
        ERROR_HANDLER.assert_true(os.path.isdir(workdir), "workdir missing", \
                                                                    __file__)
        # For system tests there might be different users
        # Make sure that the next files are accessible by anyone
        os.chmod(workdir, 0o777)

        self.testsplit_wrapper_file = os.path.join(workdir, \
                                                'test_split_wrapper.sh')
        self.counting_file = os.path.join(workdir, \
                                                    'test_split_counter')
        self.splittest_args = os.path.join(workdir, \
                                                    'splittests_args')
        with open(self.testsplit_wrapper_file, 'w') as f:
            f.write("#! /bin/bash\n")
            f.write('set -u\n')
            f.write("count=$(/bin/cat {})\n".format(self.counting_file))
            f.write("count=$(($count + 1))\n")
            f.write("/bin/echo $count > {}\n".format(self.counting_file))
            f.write('/bin/echo " ${{@:1}}" >> {}\n'.format(\
                                                        self.splittest_args))
            f.write(\
                '$MUTERIA_SYSTEM_WRAPPER_W_DEFAULT_TOOL_ABS_NAME "${@:1}"\n')
        os.chmod(self.testsplit_wrapper_file, 0o775)

        new_exe_path_map = dict(exe_path_map)
        ERROR_HANDLER.assert_true(len(new_exe_path_map) == 1, \
                                "Only single executable is supported"
                                + " for wrapper test splitting", __file__)
        for k in new_exe_path_map:
            new_exe_path_map[k] = self.testsplit_wrapper_file
        return new_exe_path_map
    #~ def set_wrapper()

    def switch_to_new_test(self):
        """ reset the counters
        """
        with open(self.counting_file, 'w') as f:
            f.write('-1\n')
        if os.path.isfile(self.splittest_args):
            os.remove(self.splittest_args)
    #~ def switch_to_new_test()

    def collect_data(self):
        """ get number of sub tests and args
        """
        ERROR_HANDLER.assert_true(os.path.isfile(self.splittest_args), \
                            "No args file ({}) during wrapper test split."\
                                .format(self.splittest_args) + \
                        "Does the test have permission to write in repo dir?",\
                                                                     __file__)
        with open(self.counting_file) as f:
            max_id = int(f.read())
            n_subtest = max_id + 1
        with open(self.splittest_args) as f:
            args = f.read().splitlines()
        return n_subtest, args
    #~ def collect_data()

    def cleanup(self):
        """ Clean the temps
        """
        for fn in [self.testsplit_wrapper_file, self.counting_file, \
                                                        self.splittest_args]:
            if os.path.isfile(fn):
                os.remove(fn)
    #~ def cleanup()
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