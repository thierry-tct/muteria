import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

ERROR_HANDLER = common_mix.ErrorHandler

class TestToolType(common_mix.EnumAutoName):
    USE_ONLY_CODE = "StaticTestcaseTool"
    USE_CODE_AND_TESTS = "DynamicTestcaseTool"

    def get_tool_type_classname(self):
        return self.get_field_value()
    #~ def get_tool_type_classname():
#~ class TestToolType

TEST_TOOL_TYPES_SCHEDULING = [
    (TestToolType.USE_ONLY_CODE,), 
    (TestToolType.USE_CODE_AND_TESTS,),
]