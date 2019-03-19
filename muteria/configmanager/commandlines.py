
from __future__ import print_function

import os
import argparse
import logging

import muteria.common.mix as common_mix 

ERROR_HANDLER = common_mix.ErrorHandler

class CommandLines(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        parser_revert = subparsers.add_parsers('revert', \
                                    help="Revert the repository to the"
                                        " initial state of the source files")
        parser_revert.add_argument("--asinitial", \
                                                help="remove also added files")

        parser_explore = subparsers.add_parsers('explore', \
                                    help="Explore the output directory"
                                        " files and folders")
        parser_explore.add_argument("--config", help="Config file")

        parser_help = subparsers.add_parsers('help', \
                                    help="Get informations of the"
                                        " framework such as tool list, ...")

        parser_run = subparsers.add_subparsers('run', \
                                    help="Execute the tass specified in the"
                                        " configuration file")
        parser_run.add_argument("--config", help="Config file")
        parser_run.add_argument("--cleanstart", \
                                            help="Clear out dir and restart")

        args = parser.parse_args()
#~ class CommandLines()