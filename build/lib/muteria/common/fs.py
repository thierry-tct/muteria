#
'''
    fs
    --
    This module implements some basic file system operation that are useful
    for loading and storing data
'''

from __future__ import print_function
import os
import json
import tarfile
import time
import shutil
import logging
import pandas as pd

import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

# JSON
def loadJSON (in_file_pathname):
    '''
    Load a Json from file and return it as a python object.

    :param in_file_pathname: Pathname of the Json file to load.
    :returns: loaded data as corresponding python object.
    '''
    with open(in_file_pathname) as fp:
        return json.load(fp)
#~ loadJSON()

def dumpJSON (data_object, out_file_pathname, pretty=False):
    '''
    Store a data object in Json format into a file.

    :param data_object: data to store in Json format. 
    :param out_file_pathname: Pathname of the Json file to store the data.
    :param pretty: Enables visual friendly layout of json file (spaces).
    :returns: None on success and error message on failure.
    '''
    with open(out_file_pathname, "w") as fp:
        if pretty:
            json.dump(data_object, fp, indent=2, sort_keys=True)
        else:
            json.dump(data_object, fp)

    return None
#~ dumpJSON()         

# CSV
def loadCSV (in_file_pathname, separator=" "):
    '''
    Load a CSV from file and return it as a pandas dataframe.

    :param in_file_pathname: Pathname of the CSV file to load.
    :param separator: The separator used in the CSV file. dafault is space.
    :returns: loaded csv data as pandas dataframe.
    '''
    return pd.read_csv(in_file_pathname, sep=separator, index_col=False)
#~ loadCSV()

def dumpCSV (dataframe, out_file_pathname, separator=" "):
    '''
    Store a dataframe in CSV format into a file.

    :param dataframe: data to store in CSV format. 
    :param out_file_pathname: Pathname of the CSV file to store the dataframe.
    :param separator: Separator used in the CSV file.
    :returns: None on success and error message on failure.
    '''
    dataframe.to_csv(out_file_pathname, sep=separator, index=False)

    return None
#~ dumpCSV()         

# TAR/UNTAR
def compressDir (in_directory, out_tarfile_pathname=None, 
                remove_in_directory=False):
    '''
    Compress (Archive) a directory to save up disk space and inodes

    :param in_directory: Directory to compress (archive). 
    :param out_tarfile_pathname: Optional Pathname of the compressed file. 
        If None, the :param:`in_directory` name is used with extension 
        `tar.gz` added.
    :param remove_in_directory: Decide whether the compressed directory
        should be deleted after compression
    :returns: None on success and an error message on failure
    '''
    if out_tarfile_pathname is None:
        out_tarfile_pathname = in_directory + ".tar.gz"

    with tarfile.open(out_tarfile_pathname, "w:gz") as tar_handle:
        tar_handle.add(in_directory, arcname='.')

    if not tarfile.is_tarfile(out_tarfile_pathname):
        errmsg = " ".join(["The created tar file", out_tarfile_pathname, \
                            "is invalid"])
        return errmsg

    if remove_in_directory:
        shutil.rmtree(in_directory)

    return None
#~ def compressDir()

def decompressDir (in_tarfile_pathname, out_directory=None, 
                    remove_in_tarfile=False):
    '''
    Decompress (UnArchive) a directory's tar file.

    :param in_tarfile_pathname: Tar file to decompress. 
    :param out_directory: Optional pathname of the destination. 
        If None, the :param:`in_tarfile_pathname` name is used 
        stripping extension `tar.gz`.
    :param remove_in_tarfile: Decide whether the decompressed file
        should be deleted after decompression
    :returns: None on success and an error message on failure
    '''
    if (in_tarfile_pathname.endswith(".tar.gz")):

        if out_directory is None:
            out_directory = in_tarfile_pathname[:-len('.tar.gz')]

        if os.path.isdir(out_directory):
            shutil.rmtree(out_directory)

        tar = tarfile.open(in_tarfile_pathname, "r:gz")
        tar.extractall(path=out_directory)
        tar.close()
        
        if not os.path.isdir(out_directory):
            errmsg = " ".join(["The out_directory", out_directory, \
                                "is missing after decompress"])
            return errmsg
#    elif (in_tarfile_pathname.endswith(".tar")):
#        if out_directory is None:
#            out_directory = in_tarfile_pathname[:-len('.tar')]
#        if os.path.isdir(out_directory):
#            shutil.rmtree(out_directory)
#        tar = tarfile.open(in_tarfile_pathname, "r:")
#        tar.extractall()
#        tar.close()
    else:
        errmsg = " ".join(["Invalid tar file:", in_tarfile_pathname])

    if remove_in_tarfile:
        os.remove(in_tarfile_pathname)

    return None
#~ def decompressDir()


class FileDirStructureHandling(object):
    '''
    Can be used for the organization of the output directory.
    Provides methods to access the files and directories
    Can get, create, remove, get_or_create files and dirs
    '''
    def __init__(self, top_dir, top_dir_key, file_dir_dict):
        self.top_dir = top_dir
        self.top_dir_key = top_dir_key
        self.error_module = ERROR_HANDLER
        self.file_dir_to_path_dict = {self.top_dir_key: '.'}
        for fd in file_dir_dict:
            if type(file_dir_dict[fd]) not in (list, tuple):
                self.error_module.error_exit(err_string="%s %s" % \
                        ("Each value in file_dir_dict", \
                        "must be an ordered list of strings"), \
                            call_location=__file__)
            if len(file_dir_dict[fd]) < 1:
                self.error_module.error_exit(err_string="%s %s" % \
                        ("empty path elements for file/dir:", fd), \
                            call_location=__file__)
            if fd in self.file_dir_to_path_dict:
                self.error_module.error_exit(err_string="%s %s %s" % \
                        ("file or directory already appears in", \
                         "self.file_dir_to_path_dict:", fd), \
                            call_location=__file__)
            # Set the relative path
            self.file_dir_to_path_dict[fd] = os.path.join(*file_dir_dict[fd])


    def resolve(self, name):
        """
        """
        if name not in self.file_dir_to_path_dict:
            self.error_module.error_exit(err_string="%s %s" % \
                                    (name, "not in file_dir_to_path_dict"), \
                                        call_location=__file__ )
        return self.file_dir_to_path_dict[name]

    def get_file_pathname(self, filename, rel_path=False):
        if rel_path:
            return self.resolve(filename)
        return os.path.normpath( \
                            os.path.join(self.top_dir, self.resolve(filename)))

    def get_existing_file_pathname(self, filename, rel_path=False):
        fullpathstring = self.get_file_pathname(filename, rel_path=False)
        if rel_path:
            retpathstring = self.get_file_pathname(filename, rel_path=True)
        else:
            retpathstring = fullpathstring
        if not os.path.isfile(fullpathstring):
            self.error_module.error_exit(err_string="%s %s" % \
                    ("getting a file non existing", fullpathstring), \
                       call_location=__file__)
        return retpathstring

    def file_exists(self, filename):
        fullpathstring = self.get_file_pathname(filename, rel_path=False)
        return os.path.isfile(fullpathstring)
        
    def remove_file_and_get(self, filename, rel_path=False):
        fullpathstring = self.get_file_pathname(filename, rel_path=False)
        if os.path.isfile(fullpathstring):
            os.remove(fullpathstring)
        if rel_path:
            return self.get_file_pathname(filename, rel_path=True)
        return fullpathstring

    def get_dir_pathname(self, dirname, rel_path=False):
        return self.get_file_pathname(dirname, rel_path)

    def dir_exists(self, dirname):
        fullpathstring = self.get_dir_pathname(dirname, rel_path=False)
        return os.path.isdir(fullpathstring)

    def get_existing_dir_pathname(self, dirname, rel_path=False):
        fullpathstring = self.get_dir_pathname(dirname, rel_path=False)
        if rel_path:
            retpathstring = self.get_dir_pathname(dirname, rel_path=True)
        else:
            retpathstring = fullpathstring
        if not os.path.isdir(fullpathstring):
            self.error_module.error_exit(err_string="%s %s" % \
                    ("getting a directory non existing", fullpathstring), \
                        call_location=__file__)
        return retpathstring

    def clean_create_and_get_dir(self, dirname, rel_path=False):
        fullpathstring = self.get_dir_pathname(dirname, rel_path=False)
        if os.path.isdir(fullpathstring):
            shutil.rmtree(fullpathstring)
        os.mkdir(fullpathstring)
        if rel_path:
            return self.get_dir_pathname(dirname, rel_path=True)
        return fullpathstring

    def get_or_create_and_get_dir(self, dirname, rel_path=False):
        fullpathstring = self.get_dir_pathname(dirname, rel_path=False)
        if not os.path.isdir(fullpathstring):
            os.makedirs(fullpathstring)
        if rel_path:
            return self.get_dir_pathname(dirname, rel_path=True)
        return fullpathstring

    def remove_dir_and_get(self, dirname, rel_path=False):
        fullpathstring = self.get_dir_pathname(dirname, rel_path=False)
        if os.path.isdir(fullpathstring):
            shutil.rmtree(fullpathstring)
        if rel_path:
            return self.get_dir_pathname(dirname, rel_path=True)
        return fullpathstring
#~ class FileDirStructureHandling()

class CheckpointState(object):
    EXEC_COMPLETED = "CHECK_POINTED_TASK_COMPLETED"
    EXEC_STARTING = "CHECK_POINTED_TASK_STARTING"
    AGG_TIME_KEY = "AGGREGATED_TIME"
    DETAILED_TIME_KEY = "DETAILED_TIME"
    CHECKPOINT_DATA_KEY = "CHECKPOINT_DATA"

    '''
        The different states are:
            - Destroyed
            - starting
            - Executing
            - Finished (Completed)
    '''
    def __init__(self, store_filepath, backup_filepath):
        self.store_filepath = store_filepath
        self.backup_filepath = backup_filepath
        # make sure that sub task are destroyed, restarted
        # when parent is. (Not necessary for finished)
        self.dep_checkpoint_states = set()
        self.started = False
        self.finished = False

        # time when the current execution started
        self.starttime = None
        
        # aggregated time loaded from last ckeckpoint (offset by starttime)
        self.prev_aggregated_time = None

        raw_obj = self._get_from_file()
        self._update_this_object(raw_obj)
    #~ def __init__()

    def get_dep_checkpoint_states(self):
        return self.dep_checkpoint_states
    #~ def get_dep_checkpoint_states()
    
    def add_dep_checkpoint_state(self, dep_cp):
        self.dep_checkpoint_states.add(dep_cp)
    #~ def add_dep_checkpoint_state()

    def destroy_checkpoint(self):
        for dep_cp in self.dep_checkpoint_states:
            dep_cp.destroy_checkpoint()
        if os.path.isfile(self.backup_filepath):
            os.remove(self.backup_filepath)
        if os.path.isfile(self.store_filepath):
            #shutil.copy2(self.store_filepath, self.backup_filepath)
            os.remove(self.store_filepath)
        self.started = False
        self.finished = False
        self.starttime = None
        self.prev_aggregated_time = None
    #~ def destroy_checkpoint()

    def set_finished(self, detailed_exectime_obj=None):
        if not self.started:
            ERROR_HANDLER.error_exit("%s" % \
                    "finishing checkpointed task while not started", __file__)
            
        self.started = False
        self.finished = True
        self.write_checkpoint(self.EXEC_COMPLETED, \
                                detailed_exectime_obj=detailed_exectime_obj)
        
        # Freeze time.
        # put this last because used in write_checkpoint
        ## update prev_aggregated_time
        self.prev_aggregated_time += (time.time() - self.starttime)
        ## invalidate startime
        self.starttime = None 
    #~ def set_finished()

    def is_destroyed(self):
        no_files = True
        for dep_cp in self.dep_checkpoint_states:
            no_files &= dep_cp.is_destroyed()
        no_files &= not os.path.isfile(self.store_filepath) and \
                    not os.path.isfile(self.backup_filepath)
        return no_files
    #~ def is_destroyed()

    def is_finished(self):
        return self.finished
    #~ def is_finished()

    def restart_task(self):
        for dep_cp in self.dep_checkpoint_states:
            dep_cp.restart_task()
        self.started = True
        self.finished = False
        self.prev_aggregated_time = 0.0
        self.starttime = time.time()
        self.write_checkpoint(self.EXEC_STARTING)
    #~ def restart_task()

    def load_checkpoint_or_start(self, ret_detailed_exectime_obj=False):
        '''
        This function also show a fresh starting of the execution
        Return None as checkpoint data if start (was not yet started)
                If ret_detailed_exectime_obj is enable, return 
                detailed_exectime_obj as second returned value
        Note: In case of continue from a checkpoint checkpoint,
                the object already in sync with files here (see __init__)
        '''
        res = None
        raw_obj = self._get_from_file()
        if raw_obj is None:
            self.restart_task()
        else:
            res = raw_obj[self.CHECKPOINT_DATA_KEY]
            if res in [self.EXEC_STARTING, self.EXEC_COMPLETED]:
                res = None
            if ret_detailed_exectime_obj:
                res = (res, raw_obj[self.DETAILED_TIME_KEY])
        return res 
    #~ def load_checkpoint_or_start()

    def write_checkpoint(self, json_obj, detailed_exectime_obj=None):
        remove_back = False
        if os.path.isfile(self.store_filepath):
            shutil.copy2(self.store_filepath, self.backup_filepath)
        else:
            remove_back = True
        cur_agg_time = \
                    self.prev_aggregated_time + (time.time() - self.starttime)
        raw_obj = { \
                    self.AGG_TIME_KEY: cur_agg_time, \
                    self.DETAILED_TIME_KEY: detailed_exectime_obj, \
                    self.CHECKPOINT_DATA_KEY: json_obj, \
        }
        dumpJSON(raw_obj, self.store_filepath, pretty=True)
        if remove_back and os.path.isfile(self.backup_filepath):
            os.remove(self.backup_filepath)
    #~ def write_checkpoint()

    def get_execution_time(self):
        ERROR_HANDLER.assert_true(not self.is_destroyed(), \
                                "Trying to get time for destroyed checkpoint",
                                                                    __file__)
        if self.starttime is None:
            return self.prev_aggregated_time
        return self.prev_aggregated_time + (time.time() - self.starttime)
    #~ def get_execution_time()

    def get_detailed_execution_time(self):
        ERROR_HANDLER.assert_true(not self.is_destroyed(), \
                        "Trying to get detailed time for destroyed checkpoint",
                                                                    __file__)

        raw_obj = self._get_from_file()
        return raw_obj[self.DETAILED_TIME_KEY]
    #~ def get_detailed_execution_time()

    def _get_from_file(self):
        contain = None
        trybackup = True
        if os.path.isfile(self.store_filepath):
            try:
                contain = loadJSON(self.store_filepath)
                trybackup = False
            except ValueError:
                trybackup = True
        if trybackup and os.path.isfile(self.backup_filepath):
            try:
                contain = loadJSON(self.backup_filepath)
            except ValueError:
                ERROR_HANDLER.error_exit("%s %s" % (\
                                        "Both Checkpoint store_file and", \
                                        "backup file are invalid"), __file__)
            if not common_mix.confirm_execution("%s %s" % ( \
                        "The checkpoint store_file is invalid but backup", \
                        "is valid. Do you want to use backup?")):
                ERROR_HANDLER.error_exit("%s %s" % (\
                                    "Execution terminated due to", \
                                    "invalid Checkpoint store_file"), __file__)
        
        # Check consistency or update obj
        if contain is not None:
            for key in [self.DETAILED_TIME_KEY, self.AGG_TIME_KEY, \
                                                    self.CHECKPOINT_DATA_KEY]:
                if key not in contain:
                    file_used = self.backup_filepath if trybackup \
                                                    else self.store_filepath
                    ERROR_HANDLER.error_exit("%s (%s). %s %s" % \
                                ("Invalid checkpoint file", file_used, \
                                "do not contain the data for", key), __file__)
        return contain
    #~ def _get_from_file()

    def _update_this_object(self, raw_obj):
        if raw_obj is None:
            # Case of Destroyed state
            self.started = False
            self.finished = False
            self.starttime = None
            self.prev_aggregated_time = None
        else:
            agg_time = raw_obj[self.AGG_TIME_KEY]
            checkpoint_data = raw_obj[self.CHECKPOINT_DATA_KEY]
            if checkpoint_data == self.EXEC_STARTING:
                # Starting State
                self.started = True
                self.finished = False
                self.starttime = time.time()
            elif checkpoint_data == self.EXEC_COMPLETED:
                # Finished state
                self.started = False
                self.finished = True
                self.starttime = None
            else:
                self.started = True
                self.finished = False
                self.starttime = time.time()
            self.prev_aggregated_time = float(agg_time)
    #~ def _update_this_object() 
#~ class CheckpointState
