
from __future__ import print_function

import itertools

def getCoupledMutants (mutants_to_killingtests, failingtests, istwoways=False):
    coupled = []
    failingtests = set(failingtests)
    for m in mutants_to_killingtests:
        if len(set(mutants_to_killingtests[m]) - failingtests) == 0:
            if istwoways and len(failingtests) != len(mutants_to_killingtests[m]):
                continue
            coupled.append(m)
    return coupled
    
def getSubsumingMutants (mutants_to_killingtests, clustered=True):
    '''
        :param mutants_to_killingtests: dict having as key the mutant ID 
                                and as value the list of test killing it
        :param clustered: decides whether the subsuming mutants are returned
                        as a list of mutants or list of mutants clusters
        :returns: a tuple of (1) list of equivalent mutants
                    (2) the list of tuple of subsuming mutant (Each tuple
                    contain the mutants that are subsuming each others) or
                    list of all subsuming mutants.
    '''

    equivalent_mutants = []
    subsuming_mutants_clusters = []

    # if empty, do nothing
    if len(mutants_to_killingtests) == 0:
        return equivalent_mutants, subsuming_mutants_clusters
    
    # make sure that the tests killing are sets
    if type(mutants_to_killingtests[mutants_to_killingtests.keys()[0]]) != set:
        mutants_to_killingtests = {m: set(mutants_to_killingtests[m]) \
                                            for m in mutants_to_killingtests}

    # Create cluster list of equi-subsumptions, and equivalent mutants list
    cluster_list = []
    for mutant_id in mutants_to_killingtests:
        if len(mutants_to_killingtests[mutant_id]) == 0:
            equivalent_mutants.append(mutant_id)
        else:
            # can it fit in existing cluster:
            found = False
            for cluster in cluster_list:
                if mutants_to_killingtests[cluster[0]] == \
                                            mutants_to_killingtests[mutant_id]:
                    cluster.append(mutant_id)
                    found = True
                    break

            if not found:
                # Create its own cluster
                cluster_list.append([mutant_id])

    # sort the clusters but increating number of killing tests
    cluster_list.sort(key=lambda x: len(mutants_to_killingtests[x[0]]))

    # for each cluster in order, check if subsumed, else, add
    for cluster in cluster_list:
        subsumed = False
        for subsuming_cluster in subsuming_mutants_clusters:
            # Check subsumption
            if len(mutants_to_killingtests[subsuming_cluster[0]] - \
                    mutants_to_killingtests[cluster[0]]) == 0:
                # cluster is subsumed by subsuming_cluster, do nothing
                subsumed = True
                break

        if not subsumed:
            subsuming_mutants_clusters.append(tuple(cluster))

    if not clustered:
        tmp_list = []
        for scluster in subsuming_mutants_clusters:
            tmp_list += scluster
        subsuming_mutants_clusters = tmp_list

    return equivalent_mutants, subsuming_mutants_clusters


def getCommonSetsSizes_venn (setsElemsDict, setsize_from=None, 
                                setsize_to=None, name_delim='&', 
                                not_common=None):
    '''
        TODO: 
    '''
    if not_common is not None:
        assert type(not_common) == dict and len(not_common) == 0

    res_set = {} 
    if setsize_from is None:
        setsize_from = 1
    if setsize_to is None:
        setsize_to = len(setsElemsDict)
    ordered_keys = list(setsElemsDict)
    for setsize in range(setsize_from, setsize_to+1):
        for set_pos in itertools.combinations(range(len(ordered_keys)), setsize):
            name_key = name_delim.join([ordered_keys[i] for i in set_pos])
            assert name_key not in res_set
            res_set[name_key] = None 
            #print (set_pos, len(set_pos))
            for i in set_pos:
                if res_set[name_key] is None:
                    res_set[name_key] = set(setsElemsDict[ordered_keys[i]])
                else:
                    res_set[name_key] &= setsElemsDict[ordered_keys[i]]

            if not_common is not None:
                assert name_key not in not_common
                not_common[name_key] = {}
                for i in set_pos:
                    name_i = ordered_keys[i]
                    extra_tmp = list(set(setsElemsDict[name_i]) - res_set[name_key])
                    if len(extra_tmp) > 0:
                        not_common[name_key][name_i] = extra_tmp

    #print (res_set)
    res_num = {} 
    for v in res_set:
        res_num[v] = len(res_set[v])
    
    return res_num, res_set
#~ def getCommonSetsSizes_venn()
