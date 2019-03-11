
from __future__ import print_function

import muteria.common.mix as common_mix

from meta_mutationtool import MetaMutationTool

class MutationToolType(common_mix.EnumAutoName):
    USE_ONLY_CODE = "StaticMutationTool"

    def get_tool_type_classname(self):
        return self.get_field_value()
    #~ def get_tool_type_classname():
#~ class MutationToolType
