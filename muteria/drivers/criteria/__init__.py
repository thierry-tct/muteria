
from __future__ import print_function

import muteria.common.mix as common_mix

class CriteriaToolType(common_mix.EnumAutoName):
    USE_ONLY_CODE = "StaticCriteriaTool"
    #USE_CODE_AND_TESTS = "DynamicCriteriaTool"

    def get_tool_type_classname(self):
        return self.get_field_value()
    #~ def get_tool_type_classname():
#~ class CriteriaToolType

class TestCriteria(common_mix.EnumAutoName):
    STATEMENT_COVERAGE = "statement_coverage"
    BRANCH_COVERAGE = "branch_coverage"
    FUNCTION_COVERAGE = "function_coverage"

    MUTANT_COVERAGE = "mutant_coverage"
    WEAK_MUTATION = "weak_mutation"
    STRONG_MUTATION = "strong_mutation"
#~ class TestCriteria

CRITERIA_SEQUENCE = [
    {
        TestCriteria.STATEMENT_COVERAGE, TestCriteria.BRANCH_COVERAGE, TestCriteria.FUNCTION_COVERAGE,
    },
    {
        TestCriteria.MUTANT_COVERAGE,
    },
    {
        TestCriteria.WEAK_MUTATION,
    },
    {
        TestCriteria.STRONG_MUTATION,
    },
]
"""
"""

CRITERIA_TOOL_TYPES_SCHEDULING = [(CriteriaToolType.USE_ONLY_CODE,)]
"""
"""

CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM = [TestCriteria.STRONG_MUTATION,]
"""
"""