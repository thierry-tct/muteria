"""
    Note: The raw configuration is a configuration that has the exact
    same representation as in the file but loaded in memory as a dict. 
    (Example: module given in file still have the filename or function
            given as string to be evaluated are also still string).
    But the final conf has everything loaded and ready to use
"""

from __future__ import print_function

import os
import sys
import argparse
import logging
import importlib

import muteria.common.mix as common_mix

import muteria.drivers.criteria as criteria

import muteria.configmanager.configurations as configurations
from muteria.configmanager.configurations import CompleteConfiguration

ERROR_HANDLER = common_mix.ErrorHandler

class ConfigurationHelper(object):
    @classmethod
    def _cmd_load(cls):
        """ Return a dict of conf file path, lang,... and other conf
            The required depend on the mode used (TODO: define required by modes)
        """
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        parser_restore = subparsers.add_parsers('restore', \
                                    help="Restore the repository to the"
                                        " initial state of the source files")
        parser_restore.add_argument("--asinitial", \
                                                help="remove also added files")
        parser_restore.add_argument("--config", help="Config file")

        parser_view = subparsers.add_parsers('view', \
                                    help="View the output directory"
                                        " files and folders")
        parser_view.add_argument("--config", help="Config file")

        parser_internal = subparsers.add_parsers('internal', \
                                    help="Get informations of the"
                                        " framework such as tool list, ...")
        parser_internal.add_argument("--languages", action='store_true', \
                                help="Get the languages supported partially")

        parser_run = subparsers.add_subparsers('run', \
                                    help="Execute the tass specified in the"
                                        " configuration file")
        parser_run.add_argument("--config", help="Config file")
        parser_run.add_argument("--cleanstart", \
                                            help="Clear out dir and restart")

        args = parser.parse_args()
    #~ def _cmd_load()

    @classmethod
    def _get_available_default_raw_conf_by_language(cls, languages):
        res = {}
        for lang in languages:
            res[lang] = cls._get_default_raw_conf(lang)
        return res
    #~ def _get_available_default_raw_conf_by_language()

    @classmethod
    def _get_default_raw_conf(cls, language):
        config_default = "muteria.configmanager.defaults"
        # Get common default conf
        com_default_conf = cls._load_raw_conf_from_file(\
                    module_str=".".join([config_default, 'common_defaults']),\
                    info="common config module", \
                    must_exist=True)
        
        # Get language specific default conf
        lang_default_conf = cls._load_raw_conf_from_file(\
                module_str=".".join([config_default, 'languages', language]),\
                info="language "+language+" config module",\
                must_exist=False)

        # create an object that is an update of common_default_conf by 
        # lang_default_conf
        com_conf_dict = cls._get_object_params_vals_as_dict(com_default_conf)
        lang_conf_dict = cls._get_object_params_vals_as_dict(lang_default_conf)

        ## Make sure default has all parameters
        c_tmp = cls._get_object_params_vals_as_dict(CompleteConfiguration)
        useless = set(com_conf_dict) - set(c_tmp)
        ERROR_HANDLER.assert_true(\
                        len(useless) + len(c_tmp) == len(com_conf_dict),\
                        "Some Configs params not in common default", __file__)

        # get result
        ## remove irrelevant
        for u in useless:
            del com_conf_dict[u]
        ## update
        res = cls._get_update_left_with_right_raw_conf(com_conf_dict,\
                                                lang_conf_dict, same_key=False)
        return res
    #~ def _get_default_raw_conf()

    @staticmethod
    def _get_object_params_vals_as_dict(obj):
        """ Get all fields of obj that are not hidden
        """
        res = {}
        for param, val in list(vars(obj).items()):
            if param.startswith('_'):
                continue
            res[param] = val
        return res
    #~ def _get_object_params_vals_as_dict()

    @staticmethod
    def _load_raw_conf_from_file(module_str, info="module", must_exist=True):
        res = None
        try:
            res = importlib.import_module(module_str)
        except ImportError:
            if must_exist:
                ERROR_HANDLER.error_exit("Failed to load {} {}.".format(\
                                                info, module_str), __file__)
        except SyntaxError:
            ERROR_HANDLER.error_exit("Syntax error in {} {}.".format(\
                                                info, module_str), __file__)
        return res
    #~ def _load_raw_conf_from_file()

    @classmethod
    def _get_update_rawconf_with_file(cls, raw_conf, raw_conf_filename):
        """
        load config from file and update raw conf with its contents
        """
        path, filename = os.path.split(os.path.normpath(raw_conf_filename))
        if path:
            sys.path.insert(0, path)
        fconf = cls._load_raw_conf_from_file(filename, info="conf file", \
                                                            must_exist=True)
        if path:
            ERROR_HANDLER.assert_true(sys.path[0] == path, "BUG", __file__)
            sys.path.pop(0)
        fconf_dict = cls._get_object_params_vals_as_dict(fconf)

        # update
        res = cls._get_update_left_with_right_raw_conf(raw_conf, fconf_dict,\
                                                                same_key=False)
        return res
    #~ def _get_update_rawconf_with_file()

    @staticmethod
    def _get_update_left_with_right_raw_conf(left, right, same_key=True):
        """ Update the keys of left with the corresponding keys in right
            into a new dict and return it.
        """
        if same_key:
            ERROR_HANDLER.assert_true(set(left) == set(right), \
                                                    "different keys", __file__)
        res = dict(left)
        for k, v in list(right.items()):
            if k in res:
                res[k] = v
        return res
    #~ def _get_update_left_with_right_raw_conf()

    @classmethod
    def get_extend_file_raw_conf(cls, raw_conf_file, language):
        """ Take a raw conf file that might not have all the parameters and 
            load, then add the missing with default value into a new 
            returned raw conf
        """
        def_conf = cls._get_default_raw_conf(language)
        res = cls._get_update_rawconf_with_file(def_conf, raw_conf_file)
        return res
    #~ def get_extend_file_raw_conf()

    @classmethod
    def get_extend_raw_conf(cls, raw_conf, language):
        """ Take a raw conf that might not have all the parameters and 
            add the missing with default value into a new returned raw conf
        """
        def_conf = cls._get_default_raw_conf(language)
        res = cls._get_update_left_with_right_raw_conf(def_conf, raw_conf, \
                                                                same_key=False)
        return res
    #~ def get_extend_raw_conf()
        
    @classmethod
    def get_cmd_raw_conf(cls):
        """ Get CLI raw configuration by parsing command line arguments
        """
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def get_cmd_raw_conf()

    @classmethod
    def _make_conf_class_from_dict(cls, dict_obj):
        cc = CompleteConfiguration()
        ERROR_HANDLER.assert_true(set(dict_obj) == set(\
                                    cls._get_object_params_vals_as_dict(cc)), \
                                                "config missmatch", __file__)
        for k, v in list(dict_obj.items()):
            setattr(cc, k, v)
        return cc
    #~ def _make_conf_class_from_dict()

    @classmethod
    def get_finalconf_from_rawconf(cls, raw_conf):
        """ Transform a raw conf into final conf
        """
        conf = cls._make_conf_class_from_dict(raw_conf)
        
        conf.ENABLED_CRITERIA = [getattr(criteria.TestCriteria, c) \
                                                for c in conf.ENABLED_CRITERIA]
        
        tmp = conf.TESTCASE_TOOLS_CONFIGS
        conf.TESTCASE_TOOLS_CONFIGS = []
        tuc = 'tool_user_custom'
        for tc in tmp:
            if tc[tuc]:
                tc[tuc] = configurations.ToolUserCustom(**tc[tuc])
            else:
                tc[tuc] = None
            conf.TESTCASE_TOOLS_CONFIGS.append(\
                                    configurations.TestcaseToolsConfig(**tc))

        # NEXT here
        #TODO: Create what need to be created (like tool confs)
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def get_finalconf_of_rawconf()

#~ class ConfigurationHelper()