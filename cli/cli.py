
from __future__ import print_function

import sys
import os
import argparse

import muteria.common.mix as common_mix

import muteria.configmanager.configurations as configurations
import muteria.configmanager.helper as configs_helper
from muteria.controller.main_controller import MainController

ERROR_HANDLER = common_mix.ErrorHandler


class CliUserInterface(object):
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
    def get_cmd_raw_conf(cls):
        """ Get CLI raw configuration by parsing command line arguments
        """
        #TODO
        ERROR_HANDLER.error_exit("FIXME: TODO: Implement the internal")
    #~ def get_cmd_raw_conf()

    def cmd_main(cls):
        # XXX Parse the arguments and get the raw configs
        cmd_raw_conf = get_cmd_raw_conf()
        
        # Call raw_config_main with the created raw config
        MainController.raw_config_main(raw_config=cmd_raw_conf)
    #~ def cmd_main()

#~ class CliUserInterface