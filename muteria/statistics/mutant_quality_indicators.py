from __future__ import print_function

import muteria.statistics.algorithms as algorithms
import muteria.common.matrices as common_matrices
import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

def _filter_out_tests (all_tests, selected_tests, mutants_to_killing_tests):
    """ Update mutants_to_killing_tests dict according to selected_tests
    """
    ERROR_HANDLER.assert_true(type(selected_tests) in (list, tuple, set)\
                and len(selected_tests) > 0, \
                "misformed selected_tests ({})".format(selected_tests), \
                                                                __file__)
    selected_tests = set(selected_tests)
    tests_diff = selected_tests - set(all_tests)
    ERROR_HANDLER.assert_true(len(tests_diff) == 0, \
            "Some specified tests are not in the matrix ({})".format(\
                                                tests_diff), __file__)
    
    for mut, killtests in mutants_to_killing_tests.items():
        mutants_to_killing_tests[mut] = \
                                    list(set(killtests) & selected_tests)
#~ def _filter_out_tests()

def getSubsumingMutants (mutant_kill_matrix_file, clustered=True, \
                                                        selected_tests=None):
    """ Get the subsuming mutants from the matrix file

        :returns: a tuple of (1) list of equivalent mutants
                    (2) the list of tuple of subsuming mutant (Each tuple
                    contain the mutants that are subsuming each others) or
                    list of all subsuming mutants.
    """
    # load matrix
    matrix = common_matrices.ExecutionMatrix(mutant_kill_matrix_file)

    # get mutants_to_killing_tests
    mutants_to_killing_tests = matrix.query_active_columns_of_rows()

    if selected_tests is not None:
        _filter_out_tests(matrix.get_nonkey_colname_list(), selected_tests, \
                                                mutants_to_killing_tests)
    return algorithms.getSubsumingMutants(mutants_to_killing_tests, \
                                                        clustered=clustered)
#~ def getSubsumingMutants ()

def getHardToKillMutants (mutant_kill_matrix_file, threshold=0.025, \
                                                        selected_tests=None):
    """ Return the pair of kill ratio and list of hard to kill mutant (kill by less than threshold
        proportion of test, 0 < threshold < 1 ).
    """

    # check threshold
    ERROR_HANDLER.assert_true(threshold > 0 and threshold < 1, \
                            "Invalid threshold, must be in interval (0,1)", \
                                                                __file__)

    # load matrix
    matrix = common_matrices.ExecutionMatrix(mutant_kill_matrix_file)

    # get mutants_to_killing_tests
    mutants_to_killing_tests = matrix.query_active_columns_of_rows()

    all_tests = matrix.get_nonkey_colname_list()
    if selected_tests is not None:
        _filter_out_tests(all_tests, selected_tests, mutants_to_killing_tests)
        all_tests = selected_tests
    
    killratio = {}
    for mut, killtests in mutants_to_killing_tests.items():
        if len(killtests) == 0:
            killratio[mut] = 1
        else:
            killratio[mut] = len(killtests) * 1.0 / len(all_tests)

    return killratio, [mut for mut, h in killratio.items() if h <= threshold]
#~ def getHardToKillMutants ()

def getHardToPropagateMutants (strong_mutant_kill_matrix_file, \
                                weak_mutant_kill_matrix_file, \
                                threshold=0.10, \
                                selected_tests=None):
    """ Return the pair of propagation ratio and list of hard to propagate mutant 
        (strongly killed by less than threshold proportion of test
        that weakly kill them, 0 < threshold < 1 ).
    """

    # check threshold
    ERROR_HANDLER.assert_true(threshold > 0 and threshold < 1, \
                            "Invalid threshold, must be in interval (0,1)", \
                                                                __file__)

    # load matrix
    sm_matrix = \
            common_matrices.ExecutionMatrix(strong_mutant_kill_matrix_file)
    wm_matrix = \
            common_matrices.ExecutionMatrix(weak_mutant_kill_matrix_file)

    # get mutants_to_killing_tests
    sm_mutants_to_killing_tests = sm_matrix.query_active_columns_of_rows()
    wm_mutants_to_killing_tests = wm_matrix.query_active_columns_of_rows()

    all_tests = sm_matrix.get_nonkey_colname_list()

    ERROR_HANDLER.assert_true(set(sm_mutants_to_killing_tests) == \
                        set(wm_mutants_to_killing_tests), \
                            "strong and weak mutant killing matrices "
                            "have different mutants", __file__)
    ERROR_HANDLER.assert_true(set(all_tests) == \
                        set(wm_matrix.get_nonkey_colname_list()), \
                            "strong and weak mutant killing matrices "
                            "have different tests", __file__)

    if selected_tests is not None:
        _filter_out_tests(all_tests, selected_tests, \
                                                sm_mutants_to_killing_tests)
        _filter_out_tests(all_tests, selected_tests, \
                                                wm_mutants_to_killing_tests)
        all_tests = selected_tests
    
    dualkillratio = {}
    for mut, sm_killtests in sm_mutants_to_killing_tests.items():
        wm_killtests = wm_mutants_to_killing_tests[mut]
        if len(wm_killtests) == 0:
            dualkillratio[mut] = 1
        else:
            dualkillratio[mut] = len(sm_killtests) * 1.0 / len(wm_killtests)

    return dualkillratio, [mut for mut, h in dualkillratio.items() if h <= threshold]
#~ def getHardToPropagateMutants ()

