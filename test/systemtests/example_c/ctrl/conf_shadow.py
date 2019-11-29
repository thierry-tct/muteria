
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _conf import *
sys.path.pop(0)

import muteria.drivers.testgeneration.tools_by_languages.c.shadow_se\
                                                .shadow_se as shadow_se_module

def build_func_shadow(*args, **kwargs):
    # TODO: shadow flags 
    if args[3] is None:
        flags = []
    else:
        flags = list(args[3])
    
    klee_change_macro_file = os.path.dirname(shadow_se_module.__file__)
    flags += ['-DENABLE_SHADOW_SE', '-I'+klee_change_macro_file]
    args = tuple(args[:3]) + (flags,) + tuple(args[4:])
    return make_build_func(*args, **kwargs)
#~ def build_func_shadow()

CODE_BUILDER_FUNCTION = build_func_shadow

# shadow tests
shadow_se_test = TestcaseToolsConfig(tooltype=TestToolType.USE_CODE_AND_TESTS, toolname='shadow_se', \
                        tool_user_custom=ToolUserCustom(\
                            PATH_TO_TOOL_BINARY_DIR='/home/shadowvm/shadow/klee-change/Release+Asserts/bin/'
                        ))
shadow_se_test.set_one_test_execution_timeout(2)

# test tool list
TESTCASE_TOOLS_CONFIGS = [
        dev_test, shadow_se_test,
]
