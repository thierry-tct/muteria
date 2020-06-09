import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

from muteria.drivers.testgeneration.tools_by_languages.c.klee.driver_config \
                                                        import DriverConfigKlee

class DriverConfigShadow (DriverConfigKlee):
    def __init__(self, keep_first_test=False, gen_timeout_is_per_test=False, \
                                                                    **kwargs):
        DriverConfigKlee.__init__(self, **kwargs)
        ERROR_HANDLER.assert_true(type(keep_first_test) == bool, \
                        "invalid keep_first_test type. Must be bool", __file__)
        self.keep_first_test = keep_first_test
        self.gen_timeout_is_per_test = gen_timeout_is_per_test
    #~ def __init__()

    def get_keep_first_test(self):
        return self.keep_first_test
    #~ def get_keep_first_test()
    
    def get_gen_timeout_is_per_test(self):
        return self.gen_timeout_is_per_test
    #~ def get_gen_timeout_is_per_test()
#~ class DriverConfigShadow
