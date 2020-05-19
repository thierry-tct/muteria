import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

class DriverConfigGCov:
    def __init__(self, allow_missing_coverage=False):
        ERROR_HANDLER.assert_true(type(allow_missing_coverage) == bool, \
                "invalid allow_missing_coverage type. Must be bool", __file__)
        self.allow_missing_coverage = allow_missing_coverage
    #~ def __init__()

    def get_allow_missing_coverage(self):
        return self.allow_missing_coverage
    #~ def get_allow_missing_coverage()
#~ class DriverConfigGCov