from __future__ import print_function
import os, sys

import unittest

import muteria.statistics.algorithms as statistics_algorithms

class Test_Subsumption(unittest.TestCase):

    def test_getSubsumingMutants_empty (self):
        # empty
        exp_eq = []
        exp_subs = []
        mutants2tests = {}
        res_eq, res_subs = statistics_algorithms.getSubsumingMutants(mutants2tests)
        self.assertEqual(res_eq, exp_eq)
        self.assertEqual(res_subs, exp_subs)

    def test_getSubsumingMutants_nonempty_clutered (self):
        # Non empty
        exp_eq = [1,9,3]
        exp_subs = [(2, 4, 10), (11,), (12, 14)]
        mutants2tests = {1:[], 2:[1,5], 3:{}, 4:[1,5], 5:[3,5,7], 6:[1,5,7], 
                            7:[3,5,7,1], 8:{1,2,3,4,5}, 9:[], 10:[1,5], 11:[3,5], 
                            12:[2], 13:[2,1], 14:[2], 15:[2,1]}
        res_eq, res_subs = statistics_algorithms.getSubsumingMutants(mutants2tests)
        self.assertEqual(set(res_eq), set(exp_eq))
        self.assertEqual(len(res_subs), len(exp_subs))
        exp_subs_set = [set (y) for y in exp_subs] 
        for r_x in res_subs:
            self.assertTrue(set(r_x) in exp_subs_set)

    def test_getSubsumingMutants_nonempty_noclustered (self):
        # Non empty
        exp_eq = [1,9,3]
        exp_subs = [2, 4, 10,  11,  12, 14]
        mutants2tests = {1:[], 2:[1,5], 3:{}, 4:[1,5], 5:[3,5,7], 6:[1,5,7], 
                            7:[3,5,7,1], 8:{1,2,3,4,5}, 9:[], 10:[1,5], 11:[3,5], 
                            12:[2], 13:[2,1], 14:[2], 15:[2,1]}
        res_eq, res_subs = statistics_algorithms.getSubsumingMutants(mutants2tests, clustered=False)
        self.assertEqual(set(res_eq), set(exp_eq))
        self.assertEqual(set(res_subs), set(exp_subs))
        
if __name__ == "__main__":
    #unittest.main()
    verbosity=2 # TODO: Check why verbosity has no effect here
    testsuite_subsumption = unittest.TestLoader().loadTestsFromTestCase(Test_Subsumption)

    unittest.TextTestRunner(verbosity=verbosity).run(testsuite_subsumption)

