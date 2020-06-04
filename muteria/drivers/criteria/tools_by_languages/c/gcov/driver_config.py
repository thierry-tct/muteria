import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

class DriverConfigGCov:
    def __init__(self, allow_missing_coverage=False, use_gdb_wrapper=True, \
                                                                    **kwargs):
        ERROR_HANDLER.assert_true(type(allow_missing_coverage) == bool, \
                "invalid allow_missing_coverage type. Must be bool", __file__)
        self.allow_missing_coverage = allow_missing_coverage
        self.use_gdb_wrapper = use_gdb_wrapper
    #~ def __init__()

    def get_allow_missing_coverage(self):
        return self.allow_missing_coverage
    #~ def get_allow_missing_coverage()
    
    def get_use_gdb_wrapper(self):
        return self.use_gdb_wrapper
    #~ def get_use_gdb_wrapper()
#~ class DriverConfigGCov
