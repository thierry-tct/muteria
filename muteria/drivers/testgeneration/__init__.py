import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

ERROR_HANDLER = common_mix.ErrorHandler

from meta_testcasetool import MetaTestcaseTool

class TestToolType(common_mix.EnumAutoName):
    USE_ONLY_CODE = "StaticTestcaseTool"
    USE_ONLY_MUTANT_CODE = "StaticMutantTestcaseTool"
    USE_CODE_AND_TESTS = "DynamicTestcaseTool"
    USE_MUTANT_CODE_AND_TESTS = "DynamicMutantTestcaseTool"

    def get_tool_type_classname(self):
        return self.get_field_value()
    #~ def get_tool_type_classname():
#~ class TestToolType