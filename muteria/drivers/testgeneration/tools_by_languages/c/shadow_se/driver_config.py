import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

class DriverConfigShadow:
    def __init__(self, keep_first_test=False):
        ERROR_HANDLER.assert_true(type(keep_first_test) == bool, \
                        "invalid keep_first_test type. Must be bool", __file__)
        self.keep_first_test = keep_first_test
    #~ def __init__()

    def get_keep_first_test(self):
        return self.keep_first_test
    #~ def get_keep_first_test()
#~ class DriverConfigShadow