from __future__ import print_function

import muteria.common.mix as common_mix

from meta_codecoveragetool import MetaCodecoverageTool

class CodecoverageToolType(common_mix.EnumAutoName):
    USE_ONLY_CODE = "StaticCodecoverageTool"

    def get_tool_type_classname(self):
        return self.get_field_value()
    #~ def get_tool_type_classname():
#~ class CodecoverageToolType

class CodecoverageType(common_mix.EnumAutoName):
    STATEMENT_KEY = "STATEMENT_COVERAGE"
    BRANCH_KEY = "BRANCH_COVERAGE"
    FUNCTION_KEY = "FUNCTION_COVERAGE"
#~ class TestToolType