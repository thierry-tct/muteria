# TODO; Transform this into unittest later on
# TODO: Test more

from __future__ import print_function

import os
import sys
thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(thisdir))))

import muteria.configmanager.helper as helper

# Test 
def test1():
    conf_help = helper.ConfigurationHelper()
    tmp_conf_file = os.path.join(thisdir, "tmp_conf.py")
    with open(tmp_conf_file, 'w') as f:
        f.write("PROGRAMMING_LANGUAGE='c'\n")
    lang = 'C'
    res = conf_help.get_extend_file_raw_conf(tmp_conf_file, lang)
    print(">>", res)
    os.remove(tmp_conf_file)
    tmp_pyc = tmp_conf_file+'c'
    if os.path.isfile(tmp_pyc):
        os.remove(tmp_pyc)

def test2():
    conf_help = helper.ConfigurationHelper()
    lang = 'C'
    tmp_rawconf = {"PROGRAMMING_LANGUAGE": lang}
    res = conf_help.get_extend_raw_conf(tmp_rawconf, lang)
    print(">>", res)

def test3():
    conf_help = helper.ConfigurationHelper()
    lang = 'C'
    tmp_rawconf = {"PROGRAMMING_LANGUAGE": lang,
                    "ENABLED_CRITERIA": ['STATEMENT_COVERAGE'],
                    "TESTCASE_TOOLS_CONFIGS": [{'tool_user_custom': None, 'tooltype': 'USE_ONLY_CODE', 'toolname': 'custom_devtests'}],
                    "CRITERIA_TOOLS_CONFIGS": [{'tool_user_custom': None, 'toolname': 'coverage_py', 'criteria_on': ["STATEMENT_COVERAGE", "BRANCH_COVERAGE"]}],
                  }
    res_raw = conf_help.get_extend_raw_conf(tmp_rawconf, lang)
    res = conf_help.get_finalconf_from_rawconf(res_raw)
    print(">>", res)
    print(">>", res.TESTCASE_TOOLS_CONFIGS[0].get_tool_name())

#-----
test1()
test2()
test3()
