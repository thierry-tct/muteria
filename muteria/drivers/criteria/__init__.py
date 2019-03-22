
from __future__ import print_function

import muteria.common.mix as common_mix

class TestCriteria(common_mix.EnumAutoName):
    STATEMENT_COVERAGE = "statement_coverage"
    BRANCH_COVERAGE = "branch_coverage"
    FUNCTION_COVERAGE = "function_coverage"

    MUTANT_COVERAGE = "mutant_coverage"
    WEAK_MUTATION = "weak_mutation"
    STRONG_MUTATION = "strong_mutation"
#~ class TestCriteria