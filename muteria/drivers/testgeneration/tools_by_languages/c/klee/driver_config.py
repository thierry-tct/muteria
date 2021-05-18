import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

class DriverConfigKlee:
    def __init__(self, no_duptest_with_seed=True, verbose_generation=False,\
                                      suppress_generation_stdout=False, **kwargs):
        ERROR_HANDLER.assert_true(type(no_duptest_with_seed) == bool, \
                "invalid no_duptest_with_seed type. Must be bool", __file__)
        ERROR_HANDLER.assert_true(type(verbose_generation) == bool, \
                "invalid verbose_generation type. Must be bool", __file__)
        ERROR_HANDLER.assert_true(type(suppress_generation_stdout) == bool, \
                "invalid suppress_generation_stdout type. Must be bool", __file__)
        self.no_duptest_with_seed = no_duptest_with_seed
        self.verbose_generation = verbose_generation
        self.suppress_generation_stdout = suppress_generation_stdout
    #~ def __init__()

    def get_gen_tests_no_dup_with_seeds (self):
        return self.no_duptest_with_seed
    #~ def get_gen_tests_no_dup_with_seeds()
    
    def get_verbose_generation (self):
        return self.verbose_generation
    #~ def get_verbose_generation()
    
    def get_suppress_generation_stdout (self):
        return self.suppress_generation_stdout
    #~ def get_suppress_generation_stdout()
#~ class DriverConfigKlee
