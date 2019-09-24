
from __future__ import print_function

import sys
import os
import argparse

from _version import __version__, _framework_name

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
        parser.add_argument('-v', '--version', action='version',
                                    version='\n{} {}\n'.format(_framework_name, 
                                                                  __version__))
        parser.add_argument("--config", help="Config file")
        parser.add_argument("--lang", help="Programming Language")
        subparsers = parser.add_subparsers(dest='command')
        parser_restore = subparsers.add_parser('restore', \
                                    help="Restore the repository to the"
                                        " initial state of the source files")
        parser_restore.add_argument("--asinitial", \
                                                help="remove also added files")

        parser_view = subparsers.add_parser('view', \
                                    help="View the output directory"
                                        " files and folders")
        parser_view.add_argument('--results', action='store_true', \
                                    help='Print the result folder location')

        parser_internal = subparsers.add_parser('internal', \
                                    help="Get informations of the"
                                        " framework such as tool list, ...")
        parser_internal.add_argument("--languages", action='store_true', \
                                help="Get the languages supported partially")

        parser_run = subparsers.add_parser('run', \
                                    help="Execute the tass specified in the"
                                        " configuration file")
        parser_run.add_argument("--cleanstart", action='store_true', \
                                            help="Clear out dir and restart")

        if len(sys.argv)==1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        args = parser.parse_args()
        return args
    #~ def _cmd_load()

    @classmethod
    def get_cmd_raw_conf(cls):
        """ Get CLI raw configuration by parsing command line arguments
        """
        args = cls._cmd_load()

        ERROR_HANDLER.assert_true(args.config, "Must specify config", __file__)
        ERROR_HANDLER.assert_true(os.path.isfile(args.config), \
                                            "Config file inexistant", __file__)
        conf_file = args.config
        cfg_obj = configs_helper.ConfigurationHelper()

        ERROR_HANDLER.assert_true(args.lang, "Must specify language", __file__)
        lang = args.lang

        raw_conf = cfg_obj.get_extend_file_raw_conf(conf_file, lang)

        if args.command == 'run':
            if args.cleanstart:
                raw_conf['EXECUTION_CLEANSTART'] = True
            raw_conf['RUN_MODE'] = configurations.SessionMode.EXECUTE_MODE
        elif args.command == 'restore':
            raw_conf['RUN_MODE'] = \
                                configurations.SessionMode.RESTORE_REPOS_MODE
        elif args.command == 'view':
            raw_conf['RUN_MODE'] = configurations.SessionMode.VIEW_MODE
        elif args.command == 'internal':
            raw_conf['RUN_MODE'] = configurations.SessionMode.INTERNAL_MODE
        else:
            ERROR_HANDLER.error_exit("must specify a command."
                            " use --help to see available commands", __file__)
        return raw_conf
    #~ def get_cmd_raw_conf()

    @classmethod
    def cmd_main(cls):
        # XXX Parse the arguments and get the raw configs
        cmd_raw_conf = cls.get_cmd_raw_conf()
        
        # Call raw_config_main with the created raw config
        ctrl = MainController()
        ctrl.raw_config_main(raw_config=cmd_raw_conf)
    #~ def cmd_main()

#~ class CliUserInterface

def main():
    CliUserInterface.cmd_main()

if __name__ == "__main__":
    main()
