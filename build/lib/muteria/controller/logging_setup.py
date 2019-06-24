""" This module contains functions to setup the logging facility.
    The logging facility make use of the standard logging lib.

    - The function `console_tmp_log_setup` set the format of the log
        to stdout to display logs before the directory containing the 
        project's log files is created. 
        (allow to pretty print status or error on stdout)
    - The function `setup` sets up the log facility to log into files.
        The function must be called only Once
"""


from __future__ import print_function

import logging
import logging.handlers

# private static variable of this module
_SETUP_DONE = False

def is_setup():
    return _SETUP_DONE
#def is_setup()

def setup(logfile=None, logconsole=False, file_level=logging.INFO, 
            console_level=logging.INFO, file_max_bytes=20000, 
            n_file_backups=1, root_name=''):

    global _SETUP_DONE

    # skip if already setup        
    if _SETUP_DONE:
        return

    # create logger 
    logger = logging.getLogger(root_name)
    logger.setLevel(min(file_level, console_level))

    # create formatter and add it to the handlers
    formatter = logging.Formatter(\
                    fmt='%(asctime)s [%(name)s] [%(levelname)s] %(message)s', \
                    datefmt='%m/%d/%Y %I:%M:%S %p')

    # create file handler?
    if logfile is not None:
        #fh = logging.FileHandler(logfile, mode='w')
        fh = logging.handlers.RotatingFileHandler(logfile, mode='a', \
                        maxBytes=file_max_bytes, backupCount=n_file_backups)
        fh.setLevel(file_level)
        fh.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)

    # create console handler?
    if logconsole:
        ch = logging.StreamHandler()
        ch.setLevel(console_level)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(ch)

    _SETUP_DONE = True
#~ def setup()

def console_tmp_log_setup(loglevel=logging.INFO, root_name=''):
    logging.basicConfig(level=loglevel, \
                format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s', \
                datefmt='%m/%d/%Y %I:%M:%S %p')
#~ def console_tmp_log_setup()
