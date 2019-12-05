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
import copy

import muteria.common.mix as common_mix

import muteria.drivers.criteria as criteria
import muteria.drivers.testgeneration as testgeneration

import muteria.drivers.optimizers.criteriatestexecution.optimizerdefs as \
                                                                crit_opt_module

import muteria.configmanager.configurations as configurations
from muteria.configmanager.configurations import CompleteConfiguration
from muteria.configmanager.configurations import ConfigElement

import muteria.controller.checkpoint_tasks as checkpoint_tasks

ERROR_HANDLER = common_mix.ErrorHandler

class ConfigurationHelper(object):

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
        ERROR_HANDLER.assert_true(com_default_conf is not None, \
                                                'invalid for comm', __file__)
        
        # Get language specific default conf
        lang_default_conf = cls._load_raw_conf_from_file(\
                module_str=".".join([config_default, 'languages', language]),\
                info="language "+language+" config module",\
                must_exist=False)

        # create an object that is an update of common_default_conf by 
        # lang_default_conf
        com_conf_dict = cls._get_object_params_vals_as_dict(com_default_conf)
        if lang_default_conf is None:
            lang_conf_dict = {}
        else:
            lang_conf_dict = \
                        cls._get_object_params_vals_as_dict(lang_default_conf)

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
        except ImportError as ie:
            if must_exist:
                ERROR_HANDLER.error_exit("{} {} {}. \n {}.".format(\
			     "Failed to load", info, module_str, str(ie)), \
                                                                   __file__)
        except SyntaxError as se:
            ERROR_HANDLER.error_exit("{} {} {}. \n {}.".format(\
                            "Syntax error in", info, module_str, str(se)), \
                                                                   __file__)
        return res
    #~ def _load_raw_conf_from_file()

    @classmethod
    def _get_update_rawconf_with_file(cls, raw_conf, raw_conf_filename):
        """
        load config from file and update raw conf with its contents
        """
        path, filename = os.path.split(os.path.normpath(\
                                        os.path.abspath(raw_conf_filename)))
        if path:
            sys.path.insert(0, path)
        ERROR_HANDLER.assert_true(filename.endswith('.py'), "{}{}{}".format(\
                                    "invalid conf file (", filename, \
                                    "). must be python source file"), __file__)
        mod_name = filename[:-len('.py')]
        fconf = cls._load_raw_conf_from_file(mod_name, info="conf file", \
                                                            must_exist=True)
        if path:
            ERROR_HANDLER.assert_true(sys.path[0] == path, "BUG", __file__)
            sys.path.pop(0)
        if fconf is None:
            fconf_dict = {}
        else:
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
    def _make_conf_class_from_dict(cls, dict_obj):
        cc = CompleteConfiguration()

        if set(dict_obj) != set(cls._get_object_params_vals_as_dict(\
                                                    CompleteConfiguration)):
            in_obj_only = set(dict_obj) - \
                                set(cls._get_object_params_vals_as_dict(\
                                                        CompleteConfiguration))
            final_templ_only = set(cls._get_object_params_vals_as_dict(\
                                        CompleteConfiguration)) - set(dict_obj)
            ERROR_HANDLER.error_exit("config missmatch: {} {}. {} {}".format(\
                            "in_obj_only", in_obj_only,
                            "final template only", final_templ_only), __file__)
        for k, v in list(dict_obj.items()):
            setattr(cc, k, v)
        return cc
    #~ def _make_conf_class_from_dict()

    @staticmethod
    def _make_tool_conf_from_raw(raw_dict_conf, tool_type_enum, 
                                default_tool_type, target_tool_class):
        tuc = 'tool_user_custom'
        ttype = 'tooltype'
        c_on = 'criteria_on'

        if ttype in raw_dict_conf:
            if raw_dict_conf[ttype]:
                ERROR_HANDLER.assert_true(\
                            hasattr(tool_type_enum, raw_dict_conf[ttype]), \
                        "Invalid test tool type: "+raw_dict_conf[ttype], \
                                                                    __file__)
                raw_dict_conf[ttype] = \
                                getattr(tool_type_enum, raw_dict_conf[ttype])
            else:
                raw_dict_conf[ttype] = default_tool_type

        if c_on in raw_dict_conf:
            if raw_dict_conf[c_on]:
                raw_dict_conf[c_on] = [getattr(criteria.TestCriteria, c) \
                                                for c in raw_dict_conf[c_on]]
            else:
                raw_dict_conf[c_on] = None

        if tuc in raw_dict_conf:
            if raw_dict_conf[tuc]:
                raw_dict_conf[tuc] = \
                            configurations.ToolUserCustom(**raw_dict_conf[tuc])
            else:
                raw_dict_conf[tuc] = None
        
        return target_tool_class(**raw_dict_conf)
    #~ def _make_tool_conf_from_raw()

    
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
    def get_finalconf_from_rawconf(cls, raw_conf):
        """ Transform a raw conf into final conf
            TODO: Verify config consistency
        """
        conf = cls._make_conf_class_from_dict(raw_conf)
        
        if conf.ENABLED_CRITERIA is None:
            conf.ENABLED_CRITERIA = \
                        copy.deepcopy(conf.CRITERIA_TOOLS_CONFIGS_BY_CRITERIA)
        tmp = []
        for c in conf.ENABLED_CRITERIA:
            if not isinstance(c, criteria.TestCriteria):
                ERROR_HANDLER.assert_true(\
                            criteria.TestCriteria.has_element_named(c), \
                            "invalid test criterion: "+c)
                c = criteria.TestCriteria[c] 
            tmp.append(c)
        conf.ENABLED_CRITERIA = tmp

        tmp = []
        for c in conf.CRITERIA_WITH_OUTPUT_SUMMARY:
            if not isinstance(c, criteria.TestCriteria):
                ERROR_HANDLER.assert_true(\
                            criteria.TestCriteria.has_element_named(c), \
                            "invalid test criterion in out sum: "+c, __file__)
                c = criteria.TestCriteria[c] 
            if c not in conf.ENABLED_CRITERIA:
                continue
            tmp.append(c)
        conf.CRITERIA_WITH_OUTPUT_SUMMARY = tmp


        if conf.CRITERIA_SEQUENCE is None:
            conf.CRITERIA_SEQUENCE = copy.deepcopy(criteria.CRITERIA_SEQUENCE)
        for pos, group in enumerate(conf.CRITERIA_SEQUENCE):
            tmp = set()
            for c in group:
                if not isinstance(c, criteria.TestCriteria):
                    ERROR_HANDLER.assert_true(\
                                criteria.TestCriteria.has_element_named(c), \
                                "invalid test criterion in seq: "+c, __file__)
                    c = criteria.TestCriteria[c] 
                if c not in conf.ENABLED_CRITERIA:
                    continue
                tmp.add(c)
            conf.CRITERIA_SEQUENCE[pos] = tmp

        
        if conf.CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM is None:
            conf.CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM = copy.deepcopy(\
                            criteria.CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM)
        tmp = []
        for c in conf.CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM:
            if not isinstance(c, criteria.TestCriteria):
                ERROR_HANDLER.assert_true(\
                            criteria.TestCriteria.has_element_named(c), \
                            "invalid test criterion in outdiff: "+c, __file__)
                c = criteria.TestCriteria[c] 
            if c not in conf.ENABLED_CRITERIA:
                continue
            tmp.append(c)
        conf.CRITERIA_REQUIRING_OUTDIFF_WITH_PROGRAM = tmp
        
        tmp = {}
        for c, sel_tech in conf.CRITERIA_ELEM_SELECTIONS.items():
            if not isinstance(c, criteria.TestCriteria):
                ERROR_HANDLER.assert_true(\
                            criteria.TestCriteria.has_element_named(c), \
                        "invalid test criterion in crit elem selection: "+c, \
                                                                    __file__)
                c = criteria.TestCriteria[c] 
            if c not in conf.ENABLED_CRITERIA:
                continue
            tmp[c] = sel_tech
        conf.CRITERIA_ELEM_SELECTIONS = tmp
        
        tmp = []
        for tc in conf.TESTCASE_TOOLS_CONFIGS:
            if not isinstance(tc, configurations.TestcaseToolsConfig):
                tc = cls._make_tool_conf_from_raw(tc, \
                            testgeneration.TestToolType,\
                            testgeneration.TEST_TOOL_TYPES_SCHEDULING[0][0],\
                            configurations.TestcaseToolsConfig)
            tmp.append(tc)
        conf.TESTCASE_TOOLS_CONFIGS = tmp

        tmp = {}
        for crit, cc_list in list(\
                            conf.CRITERIA_TOOLS_CONFIGS_BY_CRITERIA.items()):
            for cc in cc_list:
                if not isinstance(cc, configurations.CriteriaToolsConfig):
                    cc = cls._make_tool_conf_from_raw(cc, \
                            criteria.CriteriaToolType,\
                            criteria.CRITERIA_TOOL_TYPES_SCHEDULING[0][0],\
                            configurations.CriteriaToolsConfig)
            # TODO: Criteria enabled verification
            if crit not in tmp:
                tmp[crit] = []
            tmp[crit].append(cc)
        conf.CRITERIA_TOOLS_CONFIGS_BY_CRITERIA = tmp

        # criteria Optimizer
        tmp = {}
        for c, opt in conf.CRITERIA_EXECUTION_OPTIMIZERS.items():
            if not isinstance(c, criteria.TestCriteria):
                ERROR_HANDLER.assert_true(\
                            criteria.TestCriteria.has_element_named(c), \
                            "invalid test criterion in opt: "+c, __file__)
                c = criteria.TestCriteria[c] 
            if c not in conf.ENABLED_CRITERIA:
                continue
            if not isinstance(opt, crit_opt_module.CriteriaOptimizers):
                ERROR_HANDLER.assert_true(crit_opt_module.CriteriaOptimizers.\
                                                    has_element_named(opt), \
                                        "Invalid criterion Optimizer: "+opt)
                ERROR_HANDLER.assert_true(\
                                crit_opt_module.CriteriaOptimizers.\
                                                    has_element_named(opt), \
                                "invalid test criterion: "+opt)
                opt = crit_opt_module.CriteriaOptimizers[opt] 
            ERROR_HANDLER.assert_true(\
                            crit_opt_module.check_is_right_optimizer(c, opt), \
                                        "Wrong optimizer for test criterion")
            tmp[c] = opt
        # Make sure that all criteria have optimizers
        for c in conf.ENABLED_CRITERIA:
            if c not in tmp:
                tmp[c] = crit_opt_module.CriteriaOptimizers.NO_OPTIMIZATION
        conf.CRITERIA_EXECUTION_OPTIMIZERS = tmp


        tmp = []
        for ct in conf.RE_EXECUTE_FROM_CHECKPOINT_META_TASKS:
            if not isinstance(ct, checkpoint_tasks.Tasks):
                ERROR_HANDLER.assert_true(\
                            checkpoint_tasks.Tasks.has_element_named(ct), \
                            "invalid checkpoint task: "+ct)
                ct = checkpoint_tasks.Tasks[ct] 
            tmp.append(ct)
        conf.RE_EXECUTE_FROM_CHECKPOINT_META_TASKS = tmp

        # NEXT here
        #TODO: Add optimizers ....

        # make configelement for each
        for k in raw_conf:
            setattr(conf, k, ConfigElement(val=getattr(conf, k)))

        return conf
    #~ def get_finalconf_of_rawconf()

#~ class ConfigurationHelper()
