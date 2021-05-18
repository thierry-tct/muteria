import os
import muteria.common.mix as common_mix
ERROR_HANDLER = common_mix.ErrorHandler

from muteria.drivers.testgeneration.tools_by_languages.c.klee.driver_config \
                                                        import DriverConfigKlee

class MetaMuSource(common_mix.EnumAutoName):
    MART = 'mart'
    ANNOTATION = 'manual_annotation'
#~ class MetaMuSource

class DriverConfigSemu(DriverConfigKlee):
    def __init__(self, max_mutant_count_per_cluster=100,
                        meta_mutant_source=MetaMuSource.MART,
                        target_only_live_mutants=True, **kwargs):
        DriverConfigKlee.__init__(self, **kwargs)
        ERROR_HANDLER.assert_true(max_mutant_count_per_cluster > 0, \
                        "max_mutant_count_per_cluster must be > 0", __file__)
        if type(meta_mutant_source) == str \
                                    and meta_mutant_source.endswith(".bc"):
            # Consider case when directly specifying meta-mu file in semu
            ERROR_HANDLER.assert_true(os.path.isfile(meta_mutant_source), 
                    "Specified meta-mu bc file is missing: "+meta_mutant_source)
            meta_mutant_source = os.path.realpath(meta_mutant_source)
        else:
            ERROR_HANDLER.assert_true(
                MetaMuSource.is_valid(meta_mutant_source), \
                        "invalid Meta mu source. must be instance of "
                        "MetaMuSource enum", 
                __file__
            )
        self.max_mutant_count_per_cluster = max_mutant_count_per_cluster
        self.meta_mutant_source = meta_mutant_source
        self.target_only_live_mutants = target_only_live_mutants 
    #~ def __init__()

    def requires_criteria_instrumented(self):
        if type(self.meta_mutant_source) == str or meta_mutant_source == MetaMuSource.ANNOTATION:
            return False
        return True
    #~ def requires_criteria_instrumented()
    
    def get_max_mutant_count_per_cluster (self):
        return self.max_mutant_count_per_cluster
    #~ def get_max_mutant_count_per_cluster ()

    def get_meta_mutant_source (self):
        return self.meta_mutant_source
    #~ def get_meta_mutant_source ()

    def get_target_only_live_mutants(self):
        return self.target_only_live_mutants
    #~ def get_target_only_live_mutants()
#~ class DriverConfigSemu
