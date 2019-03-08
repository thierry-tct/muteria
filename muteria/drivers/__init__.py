import os
import logging
import importlib

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class ToolsModulesLoader(object):
    MUTATION_TOOLS = "MUTATION"
    TESTCASES_TOOLS = "TESTCASES"
    CODE_COVERAGE_TOOLS = "CODE_COVERAGE"

    # map of directory modules by categories 
    TOOL_CATEGORIES_DIRS = {
        MUTATION_TOOLS: "mutation",
        TESTCASES_TOOLS: "testgeneration",
        CODE_COVERAGE_TOOLS: "codecoverage"
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
