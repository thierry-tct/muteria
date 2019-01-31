import logging

def setup(logfile=None, logconsole=False, file_level=logging.INFO, 
            console_level=logging.INFO, file_max_bytes=20000, 
            n_file_backups=1, root_name=''):
    
    # create logger 
    logger = logging.getLogger(root_name)
    #logger.setLevel(logging.DEBUG)

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

 

def console_tmp_log_setup(loglevel=logging.INFO, root_name=''):
    logging.basicConfig(level=loglevel, \
                    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s', \
                    datefmt='%m/%d/%Y %I:%M:%S %p')
