
from __future__ import print_function

import os
import argparse
import logging

import muteria.common.mix as common_mix 

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
    def _get_available_default_raw_conf_by_language(cls):
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def _get_available_default_raw_conf_by_language()

    @classmethod
    def _get_default_raw_conf_file(cls, language):
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def _get_default_raw_conf_file()

    @classmethod
    def _load_raw_conf_from_file(cls, filename):
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def _load_raw_conf_from_file()

    @classmethod
    def _get_update_rawconf_with_file(cls, raw_conf, raw_conf_filename):
        """
        load config from file and update raw conf with its contents
        """
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def _get_update_rawconf_with_file()

    @classmethod
    def get_cmd_raw_conf(cls):
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def get_cmd_raw_conf()

    @classmethod
    def get_finalconf_from_rawconf(cls, raw_conf):
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def get_finalconf_of_rawconf()

#~ class ConfigurationHelper()