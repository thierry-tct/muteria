import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

class DriverConfigKlee:
    def __init__(self, no_duptest_with_seed=True, **kwargs):
        ERROR_HANDLER.assert_true(type(no_duptest_with_seed) == bool, \
                "invalid no_duptest_with_seed type. Must be bool", __file__)
        self.no_duptest_with_seed = no_duptest_with_seed
    #~ def __init__()

    def get_gen_tests_no_dup_with_seeds (self):
        return self.no_duptest_with_seed
    #~ def get_gen_tests_no_dup_with_seeds()
#~ class DriverConfigKlee