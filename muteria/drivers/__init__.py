import os
import logging
import importlib
import subprocess
import signal
import time

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix
import muteria.common.matrices as common_matrices

ERROR_HANDLER = common_mix.ErrorHandler

class ToolsModulesLoader(object):
    """ Load tools drivers
        Example:
        >>> import muteria.drivers as md
        >>> md.ToolsModulesLoader.get_tools_modules(\
        ...                            md.ToolsModulesLoader.CRITERIA_TOOLS)
        >>> {}
    """

    TESTCASES_TOOLS = "TESTCASES"
    CRITERIA_TOOLS = "CRITERIA"

    # map of directory modules by categories 
    TOOL_CATEGORIES_DIRS = {
        TESTCASES_TOOLS: "testgeneration",
        CRITERIA_TOOLS: "criteria",
    }

    # directory in each category's module that contain language folders, 
    # containing corresponding tools
    COMMON_TOOLS_BY_LANGUAGE_DIR = "tools_by_languages"

    @classmethod
    def get_tools_modules(cls, tool_category):
        '''
        Import all tools modules of the specified tool category into a Dict 
        as following:  {<language>: {<toolname>: <module>}}
        '''
        if tool_category not in cls.TOOL_CATEGORIES_DIRS:
            logging.error("%s: %s" % ("invalid tool_category", tool_category))

        modules = {}
        
        to_skip = ('__pycache__',)

        drivers_pkg_init_py = os.path.abspath(__file__)
        drivers_pkg_path = os.path.dirname(drivers_pkg_init_py)
        pkg_path = os.path.join(drivers_pkg_path, \
                                    cls.TOOL_CATEGORIES_DIRS[tool_category], \
                                    cls.COMMON_TOOLS_BY_LANGUAGE_DIR)
        language_list = []
        for lang in os.listdir(pkg_path):
            if os.path.isdir(os.path.join(pkg_path, lang)) and \
                                                        lang not in to_skip:
                language_list.append(lang.lower())

        for language in language_list:
            if '.' in language:
                ERROR_HANDLER.error_exit("%s (%s). %s" % \
                                    ("Malformed language name", language, \
                        "Language (package) name must not contain dot('.')"), \
                                                                    __file__)
            language_pkg_path = os.path.join(pkg_path, language)
            toolname_list = []
            for fd in os.listdir(language_pkg_path):
                if os.path.isdir(os.path.join(language_pkg_path, fd)) and \
                                                            fd not in to_skip:
                    toolname_list.append(fd)

            for toolname in toolname_list:
                if '.' in toolname:
                    ERROR_HANDLER.error_exit("%s (%s). %s" % \
                                    ("Malformed tool name", toolname, \
                        "Toolname (package) name must not contain dot('.')"),\
                                                                    __file__)
                    
                load_string = ".".join(['muteria', 'drivers', \
                                    cls.TOOL_CATEGORIES_DIRS[tool_category],\
                                    cls.COMMON_TOOLS_BY_LANGUAGE_DIR,\
                                                        language, toolname])

                # import the mutation tool 
                tool_pkg = importlib.import_module(load_string)

                # Add into dict
                if language not in modules:
                    modules[language] = {}
                if toolname in modules[language]:
                    logging.error("%s %s %s %s " % ("tool", toolname, \
                        "appearing multiple times for same language", language))
                    ERROR_HANDLER.error_exit()
                modules[language][toolname] = tool_pkg

        return modules
#~ class ToolsModulesLoader

class RepoFileToCustomMap(dict):
    """ This class define a mapping between a repository file and its 
    custom coresponding file. This is usefule to let the testcase tool
    know which file to replace during test execution.
    Just specify the files to change. If none is specified, the default 
    files in the repository are used.
    """

    def __init__(self):
        pass
    #~ def __init__()

    def add_map(self, repo_val, custom_val):
        ERROR_HANDLER.assert_true(repo_val not in self, \
                        "adding map failed: key {} already present.".format( \
                            repo_val), __file__)
        self[repo_val] = custom_val
    #~ def add_map()

    def update_custom_value(self, repo_val, custom_val):
        ERROR_HANDLER.assert_true(repo_val in self, \
                        "updating map failed: key {} not present.".format( \
                            repo_val), __file__)
        self[repo_val] = custom_val
    #~ def update_custom_value()

    def delete_map(self, repo_val):
        ERROR_HANDLER.assert_true(repo_val in self, \
                        "deleting map failed: key {} not present.".format( \
                            repo_val), __file__)
        del self[repo_val]
    #~ def get_custom_value()

    def get_custom_value(self, repo_val):
        ERROR_HANDLER.assert_true(repo_val in self, \
                        "getting map failed: key {} not present.".format( \
                            repo_val), __file__)
        return self[repo_val]
    #~ def get_custom_value()

    def write_to_file(self, filepath):
        common_fs.dumpJSON(self, filepath)
    #~ def write_to_file()

    def read_from_file(self, filepath):
        obj = common_fs.loadJSON(filepath)
        for k in obj:
            self.add_map(k, obj[k])
    #~ def write_to_file()
        
#~ class RepoFileToCustomMap

class DriversUtils(object):

    ################### Meta to non meta and vice versa ####################
    
    @classmethod
    def make_meta_element(cls, element, toolalias):
        return ":".join([toolalias, element])
    #~ def make_meta_element()

    @classmethod
    def reverse_meta_element(cls, meta_element):
        parts = meta_element.split(':', 1)
        assert len(parts) >= 2, "invalid meta mutant"
        toolalias, element = parts
        return toolalias, element
    #~ def reverse_meta_element()

    ############################ Subprocess Stuffs #########################
 
    # XXX sync timed out signal in retcode with used in execute_and_get...
    #EXEC_TIMED_OUT_RET_CODE = (-signal.SIGKILL, -signal.SIGTERM,) # < python 3
    EXEC_TIMED_OUT_RET_CODE = (-signal.SIGKILL.value, -signal.SIGTERM.value,)
    EXEC_SEGFAULT_OUT_RET_CODE = (-11,)

    @classmethod
    def check_tool(cls, prog, args_list=[], expected_exit_codes=[0]):
        try:
            p = subprocess.Popen([prog]+args_list, env=os.environ, \
                                             #close_fds=True, \
                                            stderr=subprocess.DEVNULL,\
                                            stdout=subprocess.DEVNULL)
            retcode = p.wait()
            if retcode not in expected_exit_codes:
                ERROR_HANDLER.error_exit("Program {} {}.".format(prog,\
                                        ': check is problematic'), __file__)
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                logging.info("{} not installed".format(prog))
                return False
            else:
                ERROR_HANDLER.error_exit("Something went wrong", __file__)
        return True
    #~ def check_tool()

    @classmethod
    def execute_and_get_retcode_out_err(cls, prog, args_list=[], \
                            env=None, timeout=None, timeout_grace_period=5, \
                            out_on=True, err_on=True, merge_err_to_out=True):
        #print(prog, args_list, env is None, timeout, out_on, err_on, merge_err_to_out)
        tmp_env = os.environ if env is None else env
        out = subprocess.PIPE if out_on else subprocess.DEVNULL
        if err_on:
            err = subprocess.STDOUT if merge_err_to_out else subprocess.PIPE
        else:
            err = subprocess.DEVNULL
        # use setsid to kill the process group
        p = subprocess.Popen([prog]+args_list, env=tmp_env, \
                                                            #close_fds=True, \
                                                        stderr=err,\
                                                        stdout=out, 
                                                        preexec_fn=os.setsid)
        try:
            stdout, stderr = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            #p.terminate() # TODO: Chose the signal to send
            os.killpg(p.pid, signal.SIGTERM)
            #p.send_signal(signal.SIGINT) # TODO: Chose the signal to send
            # give timeout_grace_period seconds to stop
            stopped = False
            for _ in range(timeout_grace_period):
                if p.poll() is None:
                    time.sleep(1)
                else:
                    stopped = True
                    break
            if not stopped:
                os.killpg(p.pid, signal.SIGKILL)
                p.kill() # TODO: Chose the signal to send
            stdout, stderr = p.communicate()
        if stdout is not None:
            stdout = stdout.decode('UTF-8', 'backslashreplace')
        if stderr is not None:
            stderr = stderr.decode('UTF-8', 'backslashreplace')
        #retcode = p.wait()
        retcode = p.poll()
        ERROR_HANDLER.assert_true(retcode is not None, \
                                "child process still running after timeout")
        return retcode, stdout, stderr
    #~ def execute_and_get_retcode_out_err()

    ############################### Misc ###################################

    @classmethod
    def update_matrix_to_cover_when_difference(cls, \
                                target_matrix_file, target_outdata_file, \
                                comparing_vector_file, comparing_outdata_file):
        ERROR_HANDLER.assert_true(target_matrix_file is not None \
                                and comparing_vector_file is not None, \
                                "target or comparing matrix is None", __file__)

        target_matrix = common_matrices.ExecutionMatrix(\
                                                filename=target_matrix_file)
        comparing_vector = common_matrices.ExecutionMatrix(\
                                                filename=comparing_vector_file)

        ERROR_HANDLER.assert_true(len(\
                            set(target_matrix.get_nonkey_colname_list()) - \
                            set(comparing_vector.get_nonkey_colname_list()) \
                                     ) == 0, "Mismatch of columns", __file__)

        # Get uncertain
        target_uncertain_cols_dict = \
                                target_matrix.query_uncertain_columns_of_rows()
        vector_uncertain_cols = \
                            comparing_vector.query_uncertain_columns_of_rows()
        vector_uncertain_cols = \
                    set(vector_uncertain_cols[list(vector_uncertain_cols)[0]])

        # Check if outdata and proceed accordingly
        if target_outdata_file is not None and \
                                            comparing_outdata_file is not None:
            # outdata are set use outdata values to decide of differences
            target_outdata = common_matrices.OutputLogData(\
                                                filename=target_outdata_file)
            vector_outdata = common_matrices.OutputLogData(\
                                            filename=comparing_outdata_file)

            _, vector_outdata_uniq = list(\
                                vector_outdata.get_zip_objective_and_data())[0]

            ## Compare using output
            timedout_key = common_matrices.OutputLogData.TIMEDOUT
            key_to_diffs = {}
            for key, key_data in target_outdata.get_zip_objective_and_data():
                intersect = set(vector_outdata_uniq) & set(key_data)
                ERROR_HANDLER.assert_true(set(key_data) == intersect, \
                            "The elements in target must all be in vector",\
                                                                    __file__)
                key_to_diffs[key] = set()
                for elem in intersect:
                    ol_equiv = common_matrices.OutputLogData.outlogdata_equiv(\
                                    key_data[elem], vector_outdata_uniq[elem])
                    if not ol_equiv:
                        key_to_diffs[key].add(elem)
        else:
            # outdata is not set use difference of matrices
            ## obtain the active cols for each rows
            target_active_cols_dict = \
                                target_matrix.query_active_columns_of_rows()
            
            vector_active_cols = \
                                comparing_vector.query_active_columns_of_rows()
            vector_active_cols = \
                        set(vector_active_cols[list(vector_active_cols)[0]])

            ## for each row of target matrix, get diff
            target_matrix_allcol = set(target_matrix.get_nonkey_colname_list())
            key_to_diffs = {}
            for row_key, row_active in target_active_cols_dict.items():
                key_to_diffs[row_key] = (set(row_active) - vector_active_cols)\
                                    | (vector_active_cols - set(row_active))
                key_to_diffs[row_key] &= target_matrix_allcol

        # Update matrix based on diff
        for key, diffs in key_to_diffs.items():
            # gather the uncertain and set to uncertain
            uncertain = vector_uncertain_cols | \
                                        set(target_uncertain_cols_dict[key])
            set_uncertain = uncertain & diffs
            diffs -= uncertain

            values = {}
            for col in set_uncertain:
                values[col] = target_matrix.getUncertainCellDefaultVal()
            for col in diffs:
                values[col] = target_matrix.getActiveCellDefaultVal()

            if len(values) > 0:
                target_matrix.update_cells(key, values)

        target_matrix.serialize()
    #~ def update_matrix_to_cover_when_difference()
#~class DriversUtils()
