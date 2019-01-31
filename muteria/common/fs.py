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
import shutil
import pandas as pd

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
    def __init__(self, top_dir, top_dir_key, file_dir_dict, error_module, \
                    log_module):
        self.top_dir = top_dir
        self.top_dir_key = top_dir_key
        self.error_module == error_module
        self.log_module = log_module
        self.file_dir_to_path_dict = {self.top_dir_key: '.'}
        for fd in file_dir_dict:
            if type(file_dir_dict[fd]) not in (list, tuple):
                self.error_module.error_exit("%s %s" % \
                        ("Each value in file_dir_dict" \
                        "must be an ordered list of strings"))
            if len(file_dir_dict[fd]) < 1:
                self.error_module.error_exit("%s %s" % \
                        ("empty path elements for file/dir:", fd))
            if fd in self.file_dir_to_path_dict:
                self.error_module.error_exit("%s %s %s" % \
                        ("file or directory already appears in", \
                         "self.file_dir_to_path_dict:", fd))
            # Set the relative path
            self.file_dir_to_path_dict[fd] = os.path.join(*file_dir_dict[fd])


    def resolve(self, name):
        if name not in self.file_dir_to_path_dict:
            self.error_module.error_exit("%s %s" % \
                                        (name, "not in file_dir_to_path_dict"))
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
            self.error_module.error_exit("%s %s" % \
                    ("getting a file non existing", fullpathstring))
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
        if rel_path:
            return self.resolve(dirname)
        return os.path.normpath( \
                            os.path.join(self.top_dir, self.resolve(dirname)))

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
            self.error_module.error_exit("%s %s" % \
                    ("getting a directory non existing", fullpathstring))
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

