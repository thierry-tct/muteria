
from __future__ import print_function

import os
import shutil

import muteria.common.mix as common_mix
import muteria.common.matrices as common_matrices

import muteria.statistics.algorithms as stats_algo

ERROR_HANDLER = common_mix.ErrorHandler

class StatsComputer(object):
    @staticmethod
    def merge_lmatrix_into_right(lmatrix_file, rmatrix_file):
        lmatrix = common_matrices.ExecutionMatrix(filename=lmatrix_file)
        if not os.path.isfile(rmatrix_file):
            shutil.copy2(lmatrix_file, rmatrix_file)
        else:
            rmatrix = common_matrices.ExecutionMatrix(filename=rmatrix_file)
            rmatrix.update_with_other_matrix(lmatrix)
            rmatrix.serialize()

    @staticmethod
    def compute_stats(config, explorer):
        ERROR_HANDLER.error_exit("TODO")
#~ class DataHandling