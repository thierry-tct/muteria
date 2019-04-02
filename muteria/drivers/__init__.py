import os
import logging
import importlib

import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class ToolsModulesLoader(object):
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
        
        drivers_pkg_init_py = os.path.abspath(__file__)
        drivers_pkg_path = os.path.dirname(drivers_pkg_init_py)
        pkg_path = os.path.join(drivers_pkg_path, \
                                    cls.TOOL_CATEGORIES_DIRS[tool_category], \
                                    cls.COMMON_TOOLS_BY_LANGUAGE_DIR)
        language_list = [lang.lower() for lang in os.listdir(pkg_path) \
                                                        if os.path.isdir(lang)]
        for language in language_list:
            if '.' in language:
                logging.error("%s (%s). %s" % ("Malformed language name", \
                        language, \
                        "Language (package) name must not contain dot('.')"))
                ERROR_HANDLER.error_exit()
            language_pkg_path = os.path.join(pkg_path, language)
            toolname_list = [fd for fd in os.listdir(language_pkg_path) \
                                                        if os.path.isdir(fd)]
            for toolname in toolname_list:
                if '.' in toolname:
                    logging.error("%s (%s). %s" % ("Malformed tool name", \
                        toolname, \
                        "Toolname (package) name must not contain dot('.')"))
                    ERROR_HANDLER.error_exit()
                load_string = ".".join([language, toolname])

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
    @classmethod
    def make_meta_element(self, element, toolalias):
        return ":".join([toolalias, element])
    #~ def make_meta_element()

    @classmethod
    def reverse_meta_element(self, meta_element):
        parts = meta_element.split(':', 1)
        assert len(parts) >= 2, "invalibd meta mutant"
        toolalias, element = parts
        return toolalias, element
    #~ def reverse_meta_element()
#~class DriversUtils()