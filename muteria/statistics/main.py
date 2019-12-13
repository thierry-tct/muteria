
from __future__ import print_function

import os
import shutil
import logging
from jinja2 import Template
import webbrowser

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs
import muteria.common.matrices as common_matrices

import muteria.statistics.algorithms as stats_algo

import muteria.controller.explorer as fd_structure

ERROR_HANDLER = common_mix.ErrorHandler

def get_subsuming_elements(matrix_file):
    mat = common_matrices.ExecutionMatrix(filename=matrix_file)
    elem_to_tests = mat.query_active_columns_of_rows()
    equiv, subs_clusters = stats_algo.getSubsumingMutants(\
                                        elem_to_tests, clustered=True)
    return equiv, subs_clusters
#~ def get_subsuming_elements()

class StatsComputer(object):
    @staticmethod
    def merge_lmatrix_into_right(lmatrix_file, rmatrix_file):
        if not os.path.isfile(rmatrix_file):
            shutil.copy2(lmatrix_file, rmatrix_file)
        else:
            lmatrix = common_matrices.ExecutionMatrix(filename=lmatrix_file)
            rmatrix = common_matrices.ExecutionMatrix(filename=rmatrix_file)
            rmatrix.update_with_other_matrix(lmatrix)
            rmatrix.serialize()
    #~ def merge_lmatrix_into_right()

    @staticmethod
    def merge_lexecoutput_into_right(lexecoutput_file, rexecoutput_file):
        if not os.path.isfile(rexecoutput_file):
            shutil.copy2(lexecoutput_file, rexecoutput_file)
        else:
            lexecoutput = common_matrices.OutputLogData(\
                                                    filename=lexecoutput_file)
            rexecoutput = common_matrices.OutputLogData(\
                                                    filename=rexecoutput_file)
            rexecoutput.update_with_other(lexecoutput)
            rexecoutput.serialize()
    #~ def merge_lmatrix_into_right()

    @staticmethod
    def compute_stats(config, explorer, checkpointer):
        # get the matrix of each test criterion
        coverages = {}
        total_to = {}
        number_of_testcases = None
        for c in config.ENABLED_CRITERIA.get_val():
            if explorer.file_exists(fd_structure.CRITERIA_MATRIX[c]):
                mat_file = explorer.get_existing_file_pathname(\
                                            fd_structure.CRITERIA_MATRIX[c])
                mat = common_matrices.ExecutionMatrix(filename=mat_file)
                row2collist = mat.query_active_columns_of_rows()
                cov = len([k for k,v in row2collist.items() if len(v) > 0])
                tot = len(row2collist)
                coverages[c.get_str()] = 'n.a.' if tot == 0 else \
                                          '{:.2f}'.format(cov * 100.0 / tot)
                total_to[c.get_str()] = tot
                if number_of_testcases is None:
                    number_of_testcases = len(mat.get_nonkey_colname_list())
        
        # JSON
        out_json = {}
        out_json['TOTAL EXECUTION TIME (s)'] = \
                                            checkpointer.get_execution_time()
        out_json['NUMBER OF TESTCASES'] = number_of_testcases
        out_json['CRITERIA'] = {}
        for c in coverages:
            out_json['CRITERIA'][c] = {'coverage': coverages[c], 
                                            '# test objectives': total_to[c]}
        common_fs.dumpJSON(out_json, explorer.get_file_pathname(\
                                            fd_structure.STATS_MAIN_FILE_JSON))

        # HTML
        template_file = os.path.join(os.path.dirname(\
                            os.path.abspath(__file__)), 'summary_report.html')
        report_file = explorer.get_file_pathname(\
                                            fd_structure.STATS_MAIN_FILE_HTML)
        
        def format_execution_time(exec_time):
            n_day = int(exec_time // (24 * 3600))
            exec_time = exec_time % (24 * 3600)
            n_hour = int(exec_time // 3600)
            exec_time %= 3600
            n_minutes = int(exec_time // 60)
            exec_time %= 60
            n_seconds = int(round(exec_time))

            res = ""
            for val, unit in [(n_day, 'day'), (n_hour, 'hour'), \
                                (n_minutes, 'minutes'), (n_seconds, 'second')]:
                if val > 0:
                    s = ' ' if val == 1 else 's '
                    res += str(val) + ' ' + unit + s
            
            return res
        #~ def format_execution_time()

        total_exec_time = format_execution_time(\
                                            checkpointer.get_execution_time())

        rendered = Template(open(template_file).read()).render( \
                                {
                                    'total_execution_time': total_exec_time,
                                    'number_of_testcases': number_of_testcases,
                                    'coverages':coverages, 
                                    'total_to':total_to,
                                })
        with open(report_file, 'w') as f:
            f.write(rendered)
        
        try:
            webbrowser.get()
            webbrowser.open('file://' + report_file,new=2)
        except Exception as e:
            logging.warning("webbrowser error: "+str(e))
    #~ def compute_stats()
#~ class DataHandling
