import os
import sys
import imp
from distutils.spawn import find_executable
import logging
import struct
import shutil
import glob

import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

ERROR_HANDLER = common_mix.ErrorHandler

from muteria.drivers import DriversUtils

from muteria.drivers.testgeneration.testcase_formats.ktest.ktest import \
                                                                KTestTestFormat

class Misc:
    @staticmethod
    def import_ktest_tool (custom_binary_dir=None):
        if custom_binary_dir is None:
            ktt_full_path = find_executable('ktest-tool')
            ERROR_HANDLER.assert_true(ktt_full_path is not None, \
                            "ktest-tool is not present on the PATH", __file__)
        else:
            ERROR_HANDLER.assert_true(os.path.isdir(custom_binary_dir), \
                            "Custom_binary_dir inexistant ({})".format(\
                                            custom_binary_dir), __file__)
            ktt_full_path = os.path.join(custom_binary_dir, 'ktest-tool')
            ERROR_HANDLER.assert_true(os.path.isfile(ktt_full_path), \
                        "ktest-tool not found in custom binary dir", __file__)
        ktest_tool = imp.load_source("ktest-tool", ktt_full_path)

        return ktest_tool
    #~ def import_ktest_tool ()
    
    @staticmethod
    def get_must_exist_dirs_of_ktests(ktest_key_to_file, custom_binary_dir=None):
        """ Takes a dict of ktest key to ktest file
            returns the dict of ktest key to list of required dirs
        """
        ktest_tool = Misc.import_ktest_tool(\
                                        custom_binary_dir=custom_binary_dir)
        ktest2reqdir = {}
        for ktest_key, ktest_file in ktest_key_to_file.items():
            # Compute the list of req_dirs
            req_dir_set = set()
            b = ktest_tool.KTest.fromfile(ktest_file)
            prev_name = None
            for ind, obj in enumerate(b.objects):
                name, data = obj
                if prev_name is not None and \
                            name == prev_name + b'-stat' and len(data) == 144:
                    # case of file stat
                    prev_name = None
                    continue
                
                prev_name = name
                
                # is it a path?
                d, f = os.path.split(os.path.normpath(name))
                if len(d) > 0 and len(f) > 0:
                    if not os.path.isabs(d):
                        ERROR_HANDLER.assert_true(b'..' not in d, \
                                "acces to parent of cur dir not allowed. " + \
                                    "ktest is {}".format(ktest_file), __file__)
                        req_dir_set.add(d.decode('UTF-8', 'backslashreplace'))
                        ERROR_HANDLER.assert_true((ind + 1) < len(b.objects), \
                              "invalid ktest, '-stat' missing " +\
                                "(ind is {}). ktest file is {}".format(\
                                                       ind, ktest_file), __file__)
                        ERROR_HANDLER.assert_true(\
                                      b.objects[ind+1][0] == (name + b"-stat"), \
                              "Invalid ktest ofr bug? ({})".format(ktest_file), \
                                                                        __file__)
                
            ktest2reqdir[ktest_key] = list(req_dir_set)
        return ktest2reqdir
    #~ def get_must_exist_dirs_of_ktests()
#~ class Misc

class FileShortNames:
    def __init__(self):
        #schar = [chr(i) for i in range(ord('A'),ord('Z')+1)\
        #                                    +range(ord('a'),ord('z')+1)]
        #ShortNames = {'names':[z[0]+z[1] for z in \
        #                    itertools.product(schar,['']+schar)], 'pos':0}

        # From KLEE: 'void klee_init_fds()' in runtime/POSIX/fd_init.c
        self.ShortNames = [bytes(chr(i), 'utf-8') for i in range(ord('A'), 256)]  
        self.pos = 0
    def reinitialize_count (self):
        self.pos = 0
    def getShortname(self): 
        self.pos += 1
        if self.pos >= len(self.ShortNames):
            ERROR_HANDLER.error_exit("too many file arguments, "
                                        "exeeded shortname list", __file__)
        return self.ShortNames[self.pos-1]
#~ class FileShortNames:

class ConvertCollectKtestsSeeds:
    tar_gz = ".tar.gz"
    test2semudirMapFile = "test2semudirMapFile.json"

    def __init__(self, custom_binary_dir=None):
        self.ktest_tool = Misc.import_ktest_tool(\
                                        custom_binary_dir=custom_binary_dir)
    #~ def __init__ ()

    def generate_seeds_from_various_ktests (self, dest_dir, \
                                            src_old_shadow_zesti_ktest_dir, \
                                   src_new_klee_ktest_dir_or_sym_args=None, \
                                            klee_ktest_is_sym_args=False, \
                                      compress_dest=True, skip_failure=False):
        """
        """

        ERROR_HANDLER.assert_true(os.path.isdir(os.path.dirname(dest_dir)), \
                                "dest dir parent does not exists", __file__)
        ERROR_HANDLER.assert_true(not os.path.isdir(dest_dir), \
                                        "dest dir already exists", __file__)
        ERROR_HANDLER.assert_true(not (compress_dest and \
                                        os.path.isfile(dest_dir+self.tar_gz)),\
                                "dest dir compressed already exists", __file__)
        
        if klee_ktest_is_sym_args:
            src_new_klee_ktest_dir = None
            klee_ktest_sym_args = src_new_klee_ktest_dir_or_sym_args
        else:
            klee_ktest_sym_args = None
            src_new_klee_ktest_dir = src_new_klee_ktest_dir_or_sym_args
            
        os.mkdir(dest_dir)

        tmpdir = os.path.join(dest_dir, '.tmp')
        os.mkdir(tmpdir)

        ERROR_HANDLER.assert_true(src_old_shadow_zesti_ktest_dir is not None \
                                    or src_new_klee_ktest_dir is not None, \
                                    "at least one src must be set", __file__)

        # decompress shadow_zesti ktest dir if compressed
        if src_old_shadow_zesti_ktest_dir is not None and \
                        src_old_shadow_zesti_ktest_dir.endswith(self.tar_gz):
            # decompress
            tmp_ar = src_old_shadow_zesti_ktest_dir
            src_old_shadow_zesti_ktest_dir = \
                            src_old_shadow_zesti_ktest_dir[:-len(self.tar_gz)]
            common_fs.TarGz.decompressDir(tmp_ar, \
                            os.path.dirname(src_old_shadow_zesti_ktest_dir), \
                                                    remove_in_archive=False)

        # decompress new_klee ktest dir if compressed
        if src_new_klee_ktest_dir is not None and \
                                src_new_klee_ktest_dir.endswith(self.tar_gz):
            # decompress
            tmp_ar = src_new_klee_ktest_dir
            src_new_klee_ktest_dir = src_new_klee_ktest_dir[:-len(self.tar_gz)]
            common_fs.TarGz.decompressDir(tmp_ar, \
                                    os.path.dirname(src_new_klee_ktest_dir), \
                                                    remove_in_archive=False)

        # Get test to zesti dir map (from the src_old... dir) TODO
        test2zestidirMap = {}
        for tc_name in os.listdir(src_old_shadow_zesti_ktest_dir):
            tc_name_dir = os.path.join(src_old_shadow_zesti_ktest_dir, tc_name)
            if os.path.isdir(tc_name_dir):
                for kleeout in os.listdir(tc_name_dir):
                    kleeout_dir = os.path.join(tc_name_dir, kleeout)
                    if os.path.isdir(kleeout_dir) \
                                and len(glob.glob(os.path.join(kleeout_dir, \
                                    "*"+KTestTestFormat.ktest_extension))) > 0:
                        test2zestidirMap[tc_name] = kleeout_dir

        # Get the seeds
        # Get sym args, convert and merge
        zest_sym_args_param = None
        zestKTContains = None
        klee_sym_args_param = None
        kleeKTContains = None

        zestKtests = []
        for tc, tcdir in test2zestidirMap.items():
            listKtestFiles = glob.glob(os.path.join(tcdir, \
                                        "*"+KTestTestFormat.ktest_extension))
            ERROR_HANDLER.assert_true(len(listKtestFiles) == 1, \
                            "Error: more than 1 or no ktest from Zesti" + \
                            " for tests: "+tc+", zestiout: "+tcdir, __file__)
            for ktestfile in listKtestFiles:
                zestKtests.append(ktestfile)
        # refactor the ktest fom zesti 
        zest_sym_args_param, zestKTContains = self._getSymArgsFromZestiKtests(\
                                                zestKtests, test2zestidirMap, \
                                                     skip_failure=skip_failure)

        # get new klee stuffs
        if src_new_klee_ktest_dir is not None:
            new_klee_test_list = []
            cwd = os.getcwd()
            os.chdir(src_new_klee_ktest_dir)
            for root, _, files in os.walk('.'):
                for f in files:
                    tc = os.path.normpath(os.path.join(root, f))
                    if tc.endswith(KTestTestFormat.ktest_extension):
                        new_klee_test_list.append(tc)
            os.chdir(cwd)
            klee_sym_args_param, kleeKTContains = \
                                    self._loadAndGetSymArgsFromKleeKTests (\
                                                    new_klee_test_list, \
                                                    src_new_klee_ktest_dir)
        elif klee_ktest_sym_args is not None:
            _, kleeKTContains = \
                            self._loadAndGetSymArgsFromKleeKTests([], None)
            klee_sym_args_param = [" ".join(l) for l in klee_ktest_sym_args]
        else:
            klee_sym_args_param, kleeKTContains = None, None
            
        sym_args_param, test2semudirMap = self._mergeZestiAndKleeKTests (\
                                        dest_dir, \
                                        zestKTContains, zest_sym_args_param, \
                                        kleeKTContains, klee_sym_args_param)
        # convert sym_args_param from this format: 
        # ["-sym-arg 1", "-sym-args 2 3 4", ...]
        # into this format:
        # [["-sym-arg", "1"], ["-sym-args", "2", "3", "4"], ...]
        sym_args_param = [g.split() for g in sym_args_param]
        common_fs.dumpJSON([sym_args_param, \
                        self._stripRootTest2Dir(dest_dir, test2semudirMap)], \
                            os.path.join(dest_dir, self.test2semudirMapFile))

        # delete tmpdir
        shutil.rmtree(tmpdir)

        # Fdupes the seedDir.
        cmd_ret, out, _ = DriversUtils.execute_and_get_retcode_out_err(\
                                        prog='fdupes',
                                        args_list=['-r', '-d', '-N', dest_dir],
                            out_on=True, err_on=True, merge_err_to_out=True)
        if cmd_ret != 0:
            ERROR_HANDLER.error_exit ("fdupes failed on SeedDir:\n{}".format(\
                                                                out), __file__)

        # compress destdir
        if compress_dest:
            common_fs.TarGz.compressDir(dest_dir, remove_in_directory=True)
    #~ def generate_seeds_from_various_ktests()

    def get_ktests_sym_args(self, ktests_dir, compressed=True):
        """ get sym args, if not there, create from ktests
        """
        if compressed:
            tmp_ar = ktests_dir
            ktests_dir = ktests_dir[:-len(self.tar_gz)]
            ERROR_HANDLER.assert_true(not os.path.isdir(ktests_dir), \
                    "make sure the uncompressed dir is abscent ({})".format(\
                                                        ktests_dir), __file__)
            common_fs.TarGz.decompressDir(tmp_ar, \
                                                os.path.dirname(ktests_dir), \
                                                    remove_in_archive=False)

        ERROR_HANDLER.assert_true(os.path.isdir(ktests_dir), \
                        "ktests dir {} is issing".format(ktests_dir), __file__)

        datfile = os.path.join(ktests_dir, self.test2semudirMapFile)
        ERROR_HANDLER.assert_true(os.path.isfile(datfile), \
                    "datfile {} is missing".format(self.test2semudirMapFile), \
                                                                    __file__)
        
        dat = common_fs.loadJSON(datfile)

        if compressed:
            shutil.rmtree(ktests_dir)

        return dat[0]
    #~ def get_ktests_sym_args()

    ##################################
    ########### PRIVATE ##############
    ##################################

    @staticmethod
    def _stripRootTest2Dir (rootdir, test2dir):
        res = {}
        for tc in test2dir:
            res[tc] = os.path.relpath(test2dir[tc], rootdir)
        return res
    #~ def _stripRootTest2Dir ()

    @staticmethod
    def _prependRootTest2Dir (rootdir, test2dir):
        res = {}
        for tc in test2dir:
            res[tc] = os.path.join(rootdir, test2dir[tc])
        return res
    #~ def _prependRootTest2Dir ()

    @staticmethod
    def _ktestToFile(ktestData, outfilename):
        """
            serialize the ktest data(ktest_tool.KTest type) into a ktest file
        """
        with open(outfilename, "wb") as f:
            f.write(b'KTEST')
            f.write(struct.pack('>i', ktestData.version))
            
            f.write(struct.pack('>i', len(ktestData.args)))
            for i in range(len(ktestData.args)):
                f.write(struct.pack('>i', len(ktestData.args[i])))
                f.write(ktestData.args[i].encode(encoding="ascii"))
            
            if ktestData.version > 2:
                f.write(struct.pack('>i', ktestData.symArgvs))
                f.write(struct.pack('>i', ktestData.symArgvLen))
            
            f.write(struct.pack('>i', len(ktestData.objects)))
            for i in range(len(ktestData.objects)):
                #name length
                f.write(struct.pack('>i', len(ktestData.objects[i][0])))
                f.write(ktestData.objects[i][0])
                #data length
                f.write(struct.pack('>i', len(ktestData.objects[i][1]))) 
                f.write(ktestData.objects[i][1])
        #print "Done ktest!"       
    #~ def _ktestToFile()

    def _parseZestiKtest(self, filename, test2zestidirMap_arg=None, \
                                                        skip_failure=False):
        """
            return a list representing the ordered list of argument 
            where each argument is represented by a pair of argtype 
            (argv or file or stdin and the corresponding sizes)
            IN KLEE, sym-files is taken into account only once (the last one)
        """

        datalist = []
        b = self.ktest_tool.KTest.fromfile(filename)
        # get the object one at the time and obtain its stuffs
        # the objects are as following: 
        #   [model_version, <the argvs> <file contain, file stat>]
        # Note that files appear in argv. 
        # here we do not have n_args because concrete (from Zesti)

        # XXX Watch this: TMP: make sure all files are at the end
        firstFile_ind = -1
        postFileArgv_ind = []
        #print(b.args) #str
        #print(b.objects) #byte
        ERROR_HANDLER.assert_true(b.objects[0][0] == b'model_version', \
                "Invalid model_version position for file: {}.\nContent:\n{}"\
                                    .format(filename, b.objects), __file__)
        #skip model_version in this loop (start from index 1)
        for pos, (name, data) in enumerate(b.objects[1:]): 
            if name == b'argv':
                if firstFile_ind >= 0:
                    postFileArgv_ind.append(pos+1)
            else:
                firstFile_ind = pos+1 if firstFile_ind < 0 else firstFile_ind
        if len(postFileArgv_ind) > 0:
            tmp_postFdat = []
            for ind_ in sorted(postFileArgv_ind, reverse=True):
                tmp_postFdat.append(b.objects[ind_])
                del b.objects[ind_]
            b.objects[firstFile_ind: firstFile_ind] = tmp_postFdat[::-1]
        #~

        # ZESTI (shadow) has issues handling forward slash(/) as argument. 
        # I think that it is a file while maybe not
        # XXX Fix that here. 
        # Since KLEE do not support directory it should be fine
        if '/' in b.args[1:]:
            for ind, (name,data) in enumerate(b.objects):
                if name == b'/':
                    if data == b'\0'*4096:
                        ERROR_HANDLER.assert_true(\
                                        b.objects[ind+1][0] == b'/-stat', \
                                        "Stat not following file", __file__)
                        del b.objects[ind:ind+2]
                    else:
                        ERROR_HANDLER.error_exit ("ERROR-BUG? data for "
                                        "forward slash not with data "
                                        "'\0'*4096 (zesti but workaround)", \
                                                                    __file__)

        seenFileStatsPos = set()
        stdin = None
        model_version_pos = -1
        fileargsposinObj_remove = []
        filesNstatsIndex = []
        maxFileSize = -1
        for ind,(name,data) in enumerate(b.objects):
            if ind in seenFileStatsPos:
                continue
            if ind == 0:
                if name != b"model_version":
                    ERROR_HANDLER.error_exit("The first argument in the "
                                    "ktest must be 'model_version'", __file__)
                else:
                    model_version_pos = ind
            else:
                # File passed , In this case, there is: 
                # (1) an ARGV obj with data the filename, 
                # (2) an Obj with name the filename and data the file data, 
                # (3) an Obj for file stat (<filename>-stat) 
                arguments = [bytes(_x, 'utf-8') for _x in b.args[1:]]
                indexes_ia = [i for i,x in enumerate(arguments) if x == name]
                
                # filename in args, the corresponding position in 
                # datalist is indexes_ia, or name is not argv but is contained.
                # example "--file=in1" TODO
                if len(indexes_ia) > 0 or name != b"argv": 
                    # in case the same name appears many times in args, 
                    # let the user manually verify
                    if len(indexes_ia) > 1:
                        if test2zestidirMap_arg is not None:
                            actual_test = None
                            for at in test2zestidirMap_arg:
                                if os.path.dirname(filename).endswith(\
                                                    test2zestidirMap_arg[at]):
                                    actual_test = at
                                    break
                            msg = " ".join(["\n>> CONFLICT: the file object",\
                                "at position ",str(ind),"with name",str(name),\
                                "in ktest",filename,"appears several times",\
                                "in args list (The actual test is:", 
                                actual_test,").\n",\
                                "    >> Please choose its space separated",\
                                "position(s), (",str(indexes_ia),"): "])
                        else:
                            msg = " ".join(["\n>> CONFLICT: the file object",\
                                "at position ",str(ind),"with name",str(name),\
                                "in ktest",filename,"appears several times",\
                                "in args list (Check",\
                                "OUTPUT/caches/test2zestidirMap.json for",\
                                "actual test).\n",\
                                "    >> Please choose its space separated",\
                                "position(s), (",str(indexes_ia),"): "])
                        raw = input(msg)
                        indinargs = [int(v) for v in raw.split()]
                        ERROR_HANDLER.assert_true(\
                                len(set(indinargs) - set(indexes_ia)) == 0, \
                                "input wrong indexes. "
                                "do not consider program name", __file__)
                    elif len(indexes_ia) == 1:
                        indinargs = indexes_ia
                    else: # name != "argv"
                        arguments = [bytes(_x, 'utf-8') for _x in b.args[1:]]
                        indexes_ia = [i for i,x in enumerate(arguments) \
                                                                if name in x]
                        if len(indexes_ia) <= 0:
                            err_msg = "Error: Must have " +\
                                    "at least one argv containing filename " +\
                                    "in its data.\n You could run with " +\
                                    "'skip_failure' enabled to neglect " +\
                                    "the error. Ktest file is "+filename
                            do_skip = False
                            if skip_failure is None:
                                do_skip = common_mix.confirm_execution(err_msg + \
                                      "\n>> DO YOU WANT TO Skip THE FAILURE? ")
                            if not do_skip and not skip_failure:
                                ERROR_HANDLER.error_exit (err_msg, __file__)
                        if len(indexes_ia) > 1:
                            if test2zestidirMap_arg is not None:
                                actual_test = None
                                for at in test2zestidirMap_arg:
                                    if os.path.dirname(filename).endswith(\
                                                    test2zestidirMap_arg[at]):
                                        actual_test = at
                                        break
                                msg = " ".join(["\n>> HINT NEEDED: the file",
                                    "object at position ",ind,"with name",\
                                    str(name),"in ktest",filename, "has file",\
                                    "with complex argv (The actual test is:",\
                                    actual_test,")."])
                            else:
                                msg = " ".join(["\n>> HINT NEEDED: the file",\
                                    "object at position ",ind,"with name",\
                                    str(name),"in ktest",filename, "has file",\
                                    "with complex argv (Check",\
                                    "OUTPUT/caches/test2zestidirMap.json",\
                                    "for actual test).\n", \
                                    "    >> Please choose its space", \
                                    "separated position(s), (",\
                                    str(indexes_ia), "):"])
                            raw = input(msg)
                            indinargs = [int(v) for v in raw.split()]
                            ERROR_HANDLER.assert_true(\
                                len(set(indinargs) - set(indexes_ia)) == 0, \
                                "input wrong indexes. do not consider "
                                "program name", __file__)
                        else:
                            indinargs = indexes_ia

                    for iv in indinargs:
                        # XXX len is 1 because this will be the file name 
                        # which is 1 char string in klee: 
                        #   'A', 'B', ... ('A' + k | 0 <= k <= 255-'A')
                        datalist[iv] = ('ARGV', 1)  

                    # ARGVs come before files in objects
                    fileargsposinObj_remove.append(indinargs)  

                    # seach for its stat, it should be the next object
                    found = False
                    if b.objects[ind + 1][0] == name + b"-stat":
                        seenFileStatsPos.add(ind + 1)
                        found = True
                    if not found:
                        ERROR_HANDLER.error_exit(\
                                "File is not having stat in ktest", __file__)

                    filesNstatsIndex += [ind, ind+1]
                    maxFileSize = max (maxFileSize, len(data))
                #elif name == "stdin-stat": #case of stdin
                #    stdin = ('STDIN', len(data)) #XXX 
                else: 
                    #ARGV
                    ERROR_HANDLER.assert_true(name == b"argv", \
                            "name ({}) not in args and not argv: {}".format(\
                                                    name, filename), __file__)
                    #XXX
                    datalist.append(('ARGV', len(data))) 

        if len(filesNstatsIndex) > 0:
            ERROR_HANDLER.assert_true(filesNstatsIndex == list(range(\
                            filesNstatsIndex[0], filesNstatsIndex[-1]+1)), \
                        "File objects are not continuous: (File {}): {}{}"\
                        .format(filename, filesNstatsIndex, list(range(\
                            filesNstatsIndex[0], filesNstatsIndex[-1]+1))),
                        __file__)

        if model_version_pos == 0:
            #for ii in range(len(fileargsposinObj_remove)):
            #    for iii in range(len(fileargsposinObj_remove[ii])):
            #        fileargsposinObj_remove[ii][iii] += 1
            # Do bothing for fileargsposinObj_remove because already 
            # indexed to not account for model version XXX
            if len(fileargsposinObj_remove) > 0:
                if len(fileargsposinObj_remove[-1]) > 0:
                    ERROR_HANDLER.assert_true(max(\
                        fileargsposinObj_remove[-1]) < filesNstatsIndex[0], \
                        "arguments do not all come before files in object", \
                        __file__)
            #-1 for model_versio which will be move to end later
            filesNstatsIndex = [(v - 1) for v in filesNstatsIndex] 

            # stdin and after files obj
            if stdin is not None:
                # -2 because of stdin and stdin-stat, -1 for mode_version
                afterLastFilenstatObj = max(filesNstatsIndex) + 1 if \
                        len(filesNstatsIndex) > 0 else (len(b.objects) - 2 -1)
                datalist.append(stdin)
            else:
                # -1 for model_version
                afterLastFilenstatObj = max(filesNstatsIndex) + 1 if \
                        len(filesNstatsIndex) > 0 else (len(b.objects) - 1) 
                # shadow-zesti have problem with stdin, \
                #use our hack on wrapper to capture that
                stdin_file = os.path.join(os.path.dirname(filename), \
                                        KTestTestFormat.STDIN_KTEST_DATA_FILE)
                ERROR_HANDLER.assert_true(os.path.isfile(stdin_file), \
                        "The stdin exported in wrapper is missing for test: "\
                        + filename, __file__)
                with open(stdin_file) as f:
                    sidat = f.read()
                    if len(sidat) > 0:
                        symin_obj = (b'stdin', bytes(sidat, 'utf-8')) #'\0'*1024)
                        syminstat_obj = (b'stdin-stat', b'\0'*144)
                        b.objects.append(symin_obj)
                        b.objects.append(syminstat_obj)
                        stdin = ('STDIN', len(sidat)) #XXX 
                        datalist.append(stdin)
        else:
            # For last, take care of putting stdin before it  
            # or last object initially"
            ERROR_HANDLER.error_exit("model version need to be either 1st", \
                                                                    __file__)

        # put 'model_version' last
        ERROR_HANDLER.assert_true(model_version_pos >= 0, \
            "'model_version' not found in ktest file: "+filename, __file__)

        b.objects.append(b.objects[model_version_pos])
        del b.objects[model_version_pos]
        
        return b, datalist, filesNstatsIndex, maxFileSize, \
                                fileargsposinObj_remove, afterLastFilenstatObj
    #~ def _parseZestiKtest()

    @staticmethod
    def _is_sym_args_having_nargs(sym_args, check_good=False):
        key_w, min_n_arg, max_n_arg, maxlen = sym_args.strip().split()
        min_n_arg, max_n_arg, maxlen = map(int, (min_n_arg, max_n_arg, maxlen))
        if check_good:
            ERROR_HANDLER.assert_true("-sym-args" in key_w, \
                            "Invalid key_w, must be having '-sym-args '", \
                            __file__)
            ERROR_HANDLER.assert_true(min_n_arg <= max_n_arg, \
                            "error: min_n_arg > max_n_arg. (bug)", __file__)
        if min_n_arg < max_n_arg:
            return True
        return False
    # def _is_sym_args_having_nargs()

    @staticmethod
    def _bestFit(outMaxVals, outNonTaken, inVals):
        assert len(inVals) <= len(outMaxVals)
        enabledArgs = [True] * len(outMaxVals)
        for i in range(len(inVals)):
            outMaxVals[i] = max(outMaxVals[i], inVals[i])
        for i in range(len(inVals), len(outMaxVals)):
            outNonTaken[i] = True
            enabledArgs[i] = False
        return enabledArgs
    #~ def _bestFit()

    def _getSymArgsFromZestiKtests (self, ktestFilesList, \
                                                    test2zestidirMap_arg, \
                                                    argv_becomes_arg_i=False, 
                                                    add_sym_stdout=False,
                                                    skip_failure=False):
        testNamesList = list(test2zestidirMap_arg.keys())
        ERROR_HANDLER.assert_true(len(ktestFilesList) == len(testNamesList), 
                "Error: size mismatch btw ktest and names: {} VS {}".format(\
                        len(ktestFilesList), len(testNamesList)), __file__)

        # XXX implement this. For program with file as parameter, 
        # make sure that the filenames are renamed in the path conditions
        # (TODO double check)
        listTestArgs = []
        ktestContains = {"CORRESP_TESTNAME":[], "KTEST-OBJ":[]}
        maxFileSize = -1
        filenstatsInObj = []
        fileArgInd = []
        afterFileNStat = []
        for ipos, ktestfile in enumerate(ktestFilesList):
            # XXX Zesti do not generate valid Ktest file when an argument 
            # is the empty string. Example tests 'basic_s18' of EXPR which 
            # is: expr "" "|" ""
            # The reson is that when writing ktest file, klee want the name 
            # to be non empty thus it fail (I think). 
            # Thus, we skip such tests here TODO: remove thes from all tests
            # so to have fair comparison with semu
            if os.system(" ".join(['ktest-tool ', ktestfile, \
                                                "> /dev/null 2>&1"])) != 0:
                logging.warning("Skipping test because Zesti generated "
                                "invalid KTEST file: " + ktestfile)
                continue
            b_tmp = self.ktest_tool.KTest.fromfile(ktestfile)
            if len(b_tmp.objects) == 0:
                logging.warning("Skipping test because Zesti "
                                "generated empty KTEST file:" + ktestfile)
                continue

            # sed because Zesti give argv, argv_1... while sym args gives 
            # arg0, arg1,...
            ktestdat, testArgs, fileNstatInd, \
                    maxFsize, fileargind, afterFnS = self._parseZestiKtest(\
                                            ktestfile, test2zestidirMap_arg, \
                                                    skip_failure=skip_failure)
            listTestArgs.append(testArgs)
            ktestContains["CORRESP_TESTNAME"].append(testNamesList[ipos])
            ktestContains["KTEST-OBJ"].append(ktestdat)
            filenstatsInObj.append(fileNstatInd)
            maxFileSize = max(maxFileSize, maxFsize)
            fileArgInd.append(fileargind)
            afterFileNStat.append(afterFnS)

        if len(listTestArgs) <= 0:
            logging.error("no ktest data, ktest PCs: " + str(ktestFilesList))
            err_msg = "No ktest data could be extracted from ktests."
            do_skip = False
            if skip_failure is None:
                do_skip = common_mix.confirm_execution(err_msg + \
                             "\n>> DO YOU WANT TO Skip THE FAILURE? ")
            if not do_skip and not skip_failure:
                ERROR_HANDLER.error_exit (err_msg, __file__)

        # update file data in objects (shortname and size)

        # divide by 2 beacause has stats
        nmax_files = int(max([len(fpv) for fpv in filenstatsInObj]) / 2) 
        if nmax_files > 0:
            shortFnames = FileShortNames().ShortNames[:nmax_files]
            for ktpos in range(len(ktestContains["CORRESP_TESTNAME"])):
                ktdat = ktestContains["KTEST-OBJ"][ktpos]

                # update file argument
                for ind_fai, fainds in enumerate(fileArgInd[ktpos]):
                    for fai in fainds:
                        # [:-1] in ktdat.objects[fai][1][-1] because of 
                        # last '\0'
                        if ktdat.objects[fai][1][:-1] == ktdat.objects\
                                    [filenstatsInObj[ktpos][2*ind_fai]][0]:
                            ktdat.objects[fai] = (ktdat.objects[fai][0], \
                                                        shortFnames[ind_fai])
                        else:
                            #print (len(ktdat.objects[fai][1]) ,\
                            #       len(ktdat.objects[filenstatsInObj[ktpos]\
                            #                               [2*ind_fai]][0])
                            #print list(ktdat.objects[fai][1]),\
                            #       list(ktdat.objects[filenstatsInObj\
                            #                        [ktpos][2*ind_fai]][0])
                            msg = " ".join(["\n>> MANUAL REPLACE: the final",\
                                "file name is "+str(shortFnames[ind_fai])+".",\
                                "initial name is "+str(ktdat.objects[\
                                filenstatsInObj[ktpos][2*ind_fai]][0])+".",
                                "\n  >> Test name is:", \
                                ktestContains["CORRESP_TESTNAME"][ktpos],\
                                "\n    >> Please replace initial file name",\
                                "with new in "+str(ktdat.objects[fai][1])+
                                " :"])
                            raw = bytes(input(msg).strip(), 'utf-8')
                            if ktdat.objects[fai][1].endswith(b'\0'):
                                raw += b'\0'
                            ktdat.objects[fai] = (ktdat.objects[fai][0], raw)

                # first add file object of additional files
                addedobj = []
                # divide by two because also has stat
                for _ in range(nmax_files - int(len(filenstatsInObj[ktpos])/2)): 
                    symf_obj = (b'', b'\0'*maxFileSize)
                    symfstat_obj = (b'-stat', b'\0'*144)
                    addedobj.append(symf_obj)
                    addedobj.append(symfstat_obj)
                insat = afterFileNStat[ktpos] 
                ktdat.objects[insat:insat] = addedobj
                filenstatsInObj[ktpos] += range(insat, insat+len(addedobj))

                # Now update the filenames and data
                for ni, fi_ in enumerate(range(0, \
                                            len(filenstatsInObj[ktpos]), 2)):
                    find_ = filenstatsInObj[ktpos][fi_]
                    fsind_ = filenstatsInObj[ktpos][fi_ + 1]
                    ERROR_HANDLER.assert_true(ktdat.objects[find_][0] \
                                    + b'-stat' == ktdat.objects[fsind_][0],
                                                        "error", __file__)
                    #file
                    ktdat.objects[find_] = (shortFnames[ni]+b"-data", \
                                        ktdat.objects[find_][1] + \
                                        b'\0'*(maxFileSize - \
                                        len(ktdat.objects[find_][1]))) 
                    #file
                    ktdat.objects[fsind_] = (shortFnames[ni]+b"-data" + \
                                        b'-stat', ktdat.objects[fsind_][1])

        # Make a general form out of listTestArgs by inserting what 
        # is needed with size 0
        # Make use of the sym-args param that can unset a param 
        # (klee care about param order)
        # Split each test args according to the FILE type (STDIN is 
        # always last), as follow: ARGV ARGV FILE ARGV FILE ...
        # then use -sym-args to flexibly set the number of enables argvs. 
        # First process the case before the first FILE, 
        # then between 1st and 2nd
        commonArgs = []
        commonArgsNumPerTest = {t: [] for t in range(len(listTestArgs))}
        testsCurFilePos = [0 for i in range(len(listTestArgs))]
        testsNumArgvs = [0 for i in range(len(listTestArgs))]
        symFileNameSize_ordered = []
        while (True):
            # Find the next non ARGV argument for all tests
            for t in range(len(testsNumArgvs)):
                nonargvfound = False
                for a in range(testsCurFilePos[t], len(listTestArgs[t])):
                    if listTestArgs[t][a][0] != "ARGV":
                        testsNumArgvs[t] = a - testsCurFilePos[t]
                        nonargvfound = True
                        break
                if not nonargvfound:
                    testsNumArgvs[t] = \
                                    len(listTestArgs[t]) - testsCurFilePos[t]
            # Rank test by num of ARGV args at this point
            indexes = list(range(len(testsNumArgvs)))
            indexes.sort(reverse=True, key=lambda x: testsNumArgvs[x])
            maxArgNum = testsNumArgvs[indexes[0]]
            maxlens = [0 for i in range(maxArgNum)]
            canDisable = [False for i in range(maxArgNum)]
            if maxArgNum > 0:
                enabledArgs = {t: None for t in range(len(testsNumArgvs))}
                for tid in indexes:
                    if testsNumArgvs[tid] == maxArgNum:
                        for pos,aid in enumerate(range(testsCurFilePos[tid], \
                                testsCurFilePos[tid] + testsNumArgvs[tid])):
                            maxlens[pos] = max(maxlens[pos], \
                                                    listTestArgs[tid][aid][1])
                        enabledArgs[tid] = [True] * maxArgNum
                    else:
                        # make the best fit on existing sizes
                        enabledArgs[tid] = self._bestFit(maxlens, canDisable, 
                                    [listTestArgs[tid][aid][1] for aid in \
                                            range(testsCurFilePos[tid], \
                                            testsCurFilePos[tid] + \
                                                        testsNumArgvs[tid])]) 
                
                # File related argument not cared about
                catchupS = len(commonArgs) - len(commonArgsNumPerTest[0])
                if catchupS > 0:
                    for t in commonArgsNumPerTest:
                        commonArgsNumPerTest[t] += [None] * catchupS

                for i in range(len(maxlens)):
                    if canDisable[i]:
                        arg = " ".join(["-sym-args 0 1", str(maxlens[i])])
                    else:
                        arg = " ".join(["-sym-arg", str(maxlens[i])])
                    # if previous is "-sym-args 0 <max-num> <size>" and 
                    # arg is also "-sym-args 0 1 <size>", with same <size>, 
                    # just update the previous
                    if len(commonArgs) > 0 \
                            and commonArgs[-1].startswith("-sym-args 0 ") \
                            and commonArgs[-1].endswith(" "+str(maxlens[i])):
                        tmpsplit = commonArgs[-1].split(' ')
                        assert len(tmpsplit) == 4
                        tmpsplit[2] = str(int(tmpsplit[2]) + 1)
                        commonArgs[-1] = " ".join(tmpsplit)
                        for t in commonArgsNumPerTest:
                            commonArgsNumPerTest[t][-1] += \
                                                        int(enabledArgs[t][i])
                    else:
                        commonArgs.append(arg)
                        for t in commonArgsNumPerTest:
                            commonArgsNumPerTest[t].append(int(\
                                                        enabledArgs[t][i]))

                # Update
                for t in range(len(testsNumArgvs)):
                    testsCurFilePos[t] += testsNumArgvs[t]

            # Process non ARGV argument stdin or file argument
            fileMaxSize =  maxFileSize
            stdinMaxSize = -1
            for t in range(len(testsNumArgvs)):
                # if the last arg was ARGV do nothing
                if testsCurFilePos[t] >= len(listTestArgs[t]):
                    continue
                # If next is FILE
                #if listTestArgs[t][testsCurFilePos[t]][0] == "FILE":
                #    fileMaxSize = max(fileMaxSize, \
                #                    listTestArgs[t][testsCurFilePos[t]][1])
                #    testsCurFilePos[t] += 1
                # If next is STDIN (last)
                #elif listTestArgs[t][testsCurFilePos[t]][0] == "STDIN":
                if listTestArgs[t][testsCurFilePos[t]][0] == "STDIN":
                    stdinMaxSize = max(stdinMaxSize, \
                                    listTestArgs[t][testsCurFilePos[t]][1])
                else:
                    ERROR_HANDLER.error_exit("unexpected arg type here: "+\
                                                "Not STDIN (type is "+\
                                listTestArgs[t][testsCurFilePos[t]][0]+")",\
                                                                    __file__)

            if fileMaxSize >= 0:
                commonArgs.append(" ".join(["-sym-files", str(nmax_files), \
                                                        str(fileMaxSize)]))
                symFileNameSize_ordered.append(fileMaxSize)
            if stdinMaxSize >= 0:
                commonArgs.append(" ".join(["-sym-stdin", str(stdinMaxSize)]))
                # Update object's stdin size. add if not present
                
                for i in range(len(ktestContains["CORRESP_TESTNAME"])):
                    siindex = len(ktestContains["KTEST-OBJ"][i].objects) - 1
                    while siindex>=0 and ktestContains["KTEST-OBJ"][i]\
                                            .objects[siindex][0] != b"stdin":
                        siindex -= 1
                    if siindex >= 0:
                        ERROR_HANDLER.assert_true(ktestContains["KTEST-OBJ"]\
                                [i].objects[siindex+1][0] == b"stdin-stat", \
                                "stdin must be followed by its stats", \
                                                                __file__)
                        pre_si_dat = \
                            ktestContains["KTEST-OBJ"][i].objects[siindex][1]
                        ktestContains["KTEST-OBJ"][i].objects[siindex] = \
                                        (b'stdin', pre_si_dat + \
                                        b"\0"*(stdinMaxSize - len(pre_si_dat)))
                    else:
                        symin_obj = (b'stdin', b'\0'*stdinMaxSize)
                        syminstat_obj = (b'stdin-stat', b'\0'*144)
                        ktestContains["KTEST-OBJ"][i].objects.insert(-1, \
                                                                    symin_obj)
                        ktestContains["KTEST-OBJ"][i].objects.insert(-1, \
                                                                syminstat_obj)
                
            break

        if add_sym_stdout:
            # Sym stdout, is this really needed
            commonArgs.append('--sym-stdout')
            # add sym-out to ktets just before the last (model_version)
            for i in range(len(ktestContains["CORRESP_TESTNAME"])):
                symout_obj = (b'stdout', b'\0'*1024)
                symoutstat_obj = (b'stdout-stat', b'\0'*144)
                ktestContains["KTEST-OBJ"][i].objects.insert(-1, symout_obj)
                ktestContains["KTEST-OBJ"][i].objects.insert(-1, \
                                                            symoutstat_obj)


        # TODO: UPDATE KTEST CONTAINS WITH NEW ARGUMENT LIST AND INSERT THE
        # "n_args" FOR '-sym-args'. ALSO PLACE 'model_version' AT THE END
        # For each Test, Change ktestContains args, go through common args 
        # and compute the different "n_args" using 'listTestArgs'  and stdin
        # stdout default.
        # Then write out the new KTEST that will be used to generate tests
        # for mutants.
        
        # XXX; The objects are ordered here in a way they the ARGV come
        # firts, then we have files, and finally model_version
        # File related argument not cared about
        catchupS = len(commonArgs) - len(commonArgsNumPerTest[0])
        if catchupS > 0:
            for t in commonArgsNumPerTest:
                commonArgsNumPerTest[t] += [None] * catchupS
        for t in commonArgsNumPerTest:
            objpos = 0
            for apos in range(len(commonArgsNumPerTest[t])):
                if commonArgs[apos].startswith("-sym-args "):
                    assert commonArgsNumPerTest[t][apos] is not None
                    if commonArgsNumPerTest[t][apos] > 0 and not \
                            ktestContains["KTEST-OBJ"][t].objects[objpos][0]\
                                                        .startswith(b"argv"):
                        logging.debug("\n\nCommonArgs: {}".format(commonArgs))
                        logging.debug("\nCommonArgsNumPerTest: {}".format(\
                                                    commonArgsNumPerTest[t]))
                        logging.debug("\nArgs: {}".format(\
                                    ktestContains["KTEST-OBJ"][t].args[1:]))
                        logging.debug("\nObjects: {}".format(\
                                    ktestContains["KTEST-OBJ"][t].objects))
                        # the name must be argv...
                        ERROR_HANDLER.error_exit(\
                                "must be argv, but found: {}".format(
                                        ktestContains["KTEST-OBJ"][t]\
                                            .objects[objpos][0]), __file__)

                    # Pad the argument data with '\0' until args maxlen
                    maxlen = int(commonArgs[apos].strip().split()[-1])
                    for sharedarg_i in range(commonArgsNumPerTest[t][apos]):
                        curlen = len(ktestContains["KTEST-OBJ"][t].objects[\
                                                    objpos + sharedarg_i][1])
                        curval = ktestContains["KTEST-OBJ"][t].objects[\
                                                        objpos + sharedarg_i]
                        #+1 Because last zero added after sym len
                        ktestContains["KTEST-OBJ"][t].objects[\
                                        objpos + sharedarg_i] = (curval[0], 
                                            curval[1]+b'\0'*(maxlen-curlen+1))

                    # Insert n_args
                    ## XXX No insertion of n_args if min_n_arg and max_n_arg 
                    # are equal
                    if self._is_sym_args_having_nargs(commonArgs[apos], \
                                                            check_good=True):
                        ktestContains["KTEST-OBJ"][t].objects.insert(\
                                    objpos, (b"n_args", struct.pack('<i', \
                                            commonArgsNumPerTest[t][apos])))       
                        objpos += 1 #pass just added 'n_args'

                    # Else no object for this, no need to advance this 
                    # (will be done bellow)
                    if commonArgsNumPerTest[t][apos] > 0: 
                        objpos += commonArgsNumPerTest[t][apos]
                # is an ARGV non file
                elif commonArgsNumPerTest[t][apos] is not None: 
                    if not ktestContains["KTEST-OBJ"][t].\
                                    objects[objpos][0].startswith(b"argv"):
                        logging.debug("\n\nCommonArgs: {}".format(commonArgs))
                        logging.debug("\nCommonArgsNumPerTest: {}".format(\
                                                    commonArgsNumPerTest[t]))
                        logging.debug("\nArgs: {}".format(\
                                    ktestContains["KTEST-OBJ"][t].args[1:]))
                        logging.debug("\nObjects: {}".format(\
                                    ktestContains["KTEST-OBJ"][t].objects))
                        # the name must be argv...
                        ERROR_HANDLER.error_exit("must be argv, but found: "\
                                    +ktestContains["KTEST-OBJ"][t].\
                                    objects[objpos][0], __file__)

                    # Pad the argument data with '\0' until args maxlen
                    maxlen = int(commonArgs[apos].strip().split(' ')[-1])
                    curlen = len(ktestContains["KTEST-OBJ"][t].\
                                                        objects[objpos][1])
                    curval = ktestContains["KTEST-OBJ"][t].objects[objpos]
                    #+1 Because last zero added after sym len
                    ktestContains["KTEST-OBJ"][t].objects[objpos] = \
                            (curval[0], curval[1]+b'\0'*(maxlen-curlen+1)) 
                    
                    objpos += 1
                else:  
                    # File or stdin, stdout
                    # TODO handle the case of files (NB: check above 
                    # how the files are recognized from zesti tests 
                    # (size may not be 0)
                    pass 

        # Change the args list in each ktest object with the common symb args 
        for ktdat in ktestContains["KTEST-OBJ"]:
            ktdat.args = ktdat.args[:1]
            for s in commonArgs:
                ktdat.args += s.strip().split(' ') 

        # Change all argv keywords into arg<i>
        if argv_becomes_arg_i:
            for ktdat in ktestContains["KTEST-OBJ"]:
                i_ = 0
                for objpos, (name, data) in enumerate(ktdat.objects):
                    if name != b"argv":
                        continue
                    ktdat.objects[objpos] = (b'arg'+bytes(str(i_), 'ascii'), \
                                                                        data)
                    i_ += 1

        return commonArgs, ktestContains
    #~ _getSymArgsFromZestiKtests()

    def _loadAndGetSymArgsFromKleeKTests(self, ktestsList, teststopdir):
        '''
            the list of klee tests (ktest names) are il ktestsList. 
            Each represent the location of the ktest w.r.t. teststopdir
        '''
        # load the ktests
        commonArgs = None
        tmpsplitcommon = None
        stdin_fixed_common = None
        ktestContains = {"CORRESP_TESTNAME":[], "KTEST-OBJ":[]}
        for kt in ktestsList:
            ktestfile = os.path.join(teststopdir, kt)
            ERROR_HANDLER.assert_true(os.path.isfile(ktestfile), \
                    "Ktest file for test is missing :" + ktestfile, __file__)

            b = self.ktest_tool.KTest.fromfile(ktestfile)
            if commonArgs is None:
                commonArgs = [] 
                # make chunk (sym-args together with its params)
                anArg = None
                tmpsplitcommon = b.args[1:]
                for c in tmpsplitcommon:
                    if c.startswith('-sym') or c.startswith('--sym'):
                        if anArg is not None:
                            commonArgs.append(anArg)
                        anArg = c
                    else:
                        anArg += " " + c
                if anArg is not None:
                    commonArgs.append(anArg)
        
                # XXX fix problem with klee regarding stdin
                a_has_stdin = False
                for sa in commonArgs:
                    if '-sym-stdin ' in sa:
                        a_has_stdin = True
                        break
                if not a_has_stdin:
                    o_stdin_len = -1
                    for o in b.objects:
                        if o[0] == b'stdin':
                            o_stdin_len = len(o[1])
                            break
                    if o_stdin_len >= 0:
                        si_pos = len(commonArgs)-1 if '-sym-stdout' in \
                                        commonArgs[-1] else len(commonArgs)
                        commonArgs.insert(si_pos, \
                                            "-sym-stdin "+str(o_stdin_len))
                        stdin_fixed_common = []
                        for s_a in commonArgs:
                            stdin_fixed_common += s_a.split()
                # make sure that model_version is the last object
                ERROR_HANDLER.assert_true(\
                                    b.objects[-1][0] == b"model_version", \
                                "The last object is not 'model_version'" + \
                                                " in klee's ktest", __file__)
            else:
                ERROR_HANDLER.assert_true(tmpsplitcommon == b.args[1:], \
                            "Sym Args are not common among KLEE's ktests", 
                                                                    __file__)
                # handle case when problem with klee and stdin
                if stdin_fixed_common is not None:
                    b.args[1:] = list(stdin_fixed_common)

            ktestContains["KTEST-OBJ"].append(b)
            ktestContains["CORRESP_TESTNAME"].append(kt)

        return commonArgs, ktestContains
    #~ def _loadAndGetSymArgsFromKleeKTests()

    def _updateObjects(self, argvinfo, ktestContains):
        '''
            Use old and new from argv_old_new to update the argv in 
            ktestContain
            Sequence in ktestobject: 
            1) argv(arg<i>), 
            2) [<ShortName>-data, <ShortName>-data-stat], 
            3) [stdin, stdin-stat], 
            4) [stdout, stdout-stat], 
            5) model_version
        '''

        def isCmdArg(name):
            if name == b'n_args' or name.startswith(b'argv') \
                                or name.startswith(b'arg'):
                return True
            return False
        #~ def isCmdArg()

        # list_new_sym_args = [(<nmin>,<nmax>,<size>),...]
        def old2new_cmdargs(objSegment, list_new_sym_args, old_has_nargs):
            res = []
            # First obj may be n_args object
            nargs = len(objSegment) - int(old_has_nargs) 
            nums = [x[0] for x in list_new_sym_args]
            n_elem = sum(nums)
            ERROR_HANDLER.assert_true(n_elem <= nargs , \
                            "min sum do not match to nargs. n_args="\
                            +str(nargs)+", min sum="+str(n_elem), __file__)
            for i in range(len(nums))[::-1]:
                rem = nargs - n_elem
                if rem <= 0:
                    break
                inc = min(rem, list_new_sym_args[i][1] - nums[i])
                n_elem += inc
                nums[i] += inc
            ERROR_HANDLER.assert_true(n_elem == nargs, \
                "n_elem must be equal to nargs here. Got: {} VS {}".format(\
                                                    n_elem, nargs), __file__)

            # put elements in res according to nums
            ao_ind = 1
            for i,n in enumerate(nums):
                if self._is_sym_args_having_nargs(" ".join(['-sym-args']\
                                    +list(map(str, list_new_sym_args[i])))):
                    res.append((b"n_args", struct.pack('<i', n)))
                for j in range(ao_ind, ao_ind+n):
                    res.append((objSegment[j][0], objSegment[j][1] \
                                         + b'\0'*(list_new_sym_args[i][2] \
                                            - len(objSegment[j][1]) + 1)))
                ao_ind += n
            assert ao_ind == len(objSegment)
            return res
        #~ def old2new_cmdargs()

        assert len(argvinfo['old']) == len(argvinfo['new'])

        argvinfo_new_extracted = []
        for vl in argvinfo['new']:
            argvinfo_new_extracted.append([])
            for v in vl:
                # assuming all args in new are sym-args (no sym-arg)
                kw, nmin, nmax, size = v.split()
                argvinfo_new_extracted[-1].append(\
                                            (int(nmin), int(nmax), int(size)))

        for okt in ktestContains['KTEST-OBJ']:
            kt_obj = okt.objects
            # First process sym-files, sym-stdin and sym-stdout
            pointer = -1 #model_version
            # sym-stdout
            if argvinfo['sym-std']['out-present']:
                if not argvinfo['sym-std']['out-present-pre']:
                    kt_obj.insert(pointer, (b'stdout', b'\0'*1024))
                    kt_obj.insert(pointer, (b'stdout-stat', b'\0'*144))
                pointer -= 2
            
            # sym-stdin
            if argvinfo['sym-std']['in-present']:
                if not argvinfo['sym-std']['in-present-pre']:
                    kt_obj.insert(pointer, \
                            (b'stdin', b'\0'*argvinfo['sym-std']['in-size']))
                    kt_obj.insert(pointer, (b'stdin-stat', b'\0'*144))
                    pointer -= 2
                elif argvinfo['sym-std']['in-size-pre'] \
                                            != argvinfo['sym-std']['in-size']:
                    # first 2 because model_version is at position -1 
                    # and secaon because of stdout-stat
                    stdin_stat_pos = pointer - 1 
                    stdin_pos = stdin_stat_pos - 1
                    ERROR_HANDLER.assert_true(\
                                        kt_obj[stdin_pos][0] == b'stdin', 
                                        "Expected stdin as object just before"
                                        "stdout and model_version", __file__)
                    kt_obj[stdin_pos] = (kt_obj[stdin_pos][0], \
                                    kt_obj[stdin_pos][1] + \
                                    b'\0'*(argvinfo['sym-std']['in-size'] - \
                                        argvinfo['sym-std']['in-size-pre']))
                    pointer -= 2
                else:
                    pointer -= 2
           
            # sym-files
            if argvinfo['sym-files']['nFiles'] > 0:
                if argvinfo['sym-files']['nFiles-pre'] > 0 and \
                                        argvinfo['sym-files']['size-pre'] \
                                            != argvinfo['sym-files']['size']:
                    for f_p in range(pointer - \
                                2*argvinfo['sym-files']['nFiles-pre'], \
                                                                pointer, 2):
                        ERROR_HANDLER.assert_true(\
                                    not isCmdArg(kt_obj[f_p][0]), \
                                    "Expected sym file object, but "+\
                                    "found cmd arg: Pos="+str(f_p)\
                                    +", object="+str(kt_obj[f_p]), __file__)
                        kt_obj[f_p] = (kt_obj[f_p][0], kt_obj[f_p][1] \
                                    + b'\0'*(argvinfo['sym-files']['size'] \
                                        - argvinfo['sym-files']['size-pre']))

                if argvinfo['sym-files']['nFiles-pre'] != \
                                            argvinfo['sym-files']['nFiles']:
                    # add empty file at position
                    snames = FileShortNames().ShortNames\
                                    [argvinfo['sym-files']['nFiles-pre']\
                                            :argvinfo['sym-files']['nFiles']]
                    for sn in snames:
                        kt_obj.insert(pointer, (sn+b'-data', \
                                        b'\0'*argvinfo['sym-files']['size']))
                        kt_obj.insert(pointer, (sn+b'-data'+b'-stat', b'\0'*144))
                pointer -= 2*argvinfo['sym-files']['nFiles']
            
            #sym cmdargv(arg)
            obj_ind = 0
            for arg_ind in range(len(argvinfo['old'])):
                #added ones, all are -sym-args, just add n_args=0
                if argvinfo['old'][arg_ind] is None: 
                    for sa in argvinfo['new'][arg_ind]:
                        ERROR_HANDLER.assert_true(\
                                        self._is_sym_args_having_nargs(sa), \
                                        "min_n_args and max_n_arg must"+\
                                        " be different here", __file__)
                        kt_obj.insert(obj_ind, \
                                            (b"n_args", struct.pack('<i', 0)))
                        obj_ind += 1
                else:
                    ERROR_HANDLER.assert_true(isCmdArg(kt_obj[obj_ind][0]), \
                        "Supposed to be CMD arg: {}".format(\
                                                kt_obj[obj_ind][0]), __file__)
                    if '-sym-arg ' in argvinfo['old'][arg_ind]:
                        ERROR_HANDLER.assert_true(\
                                    len(argvinfo['new'][arg_ind]) == 1, \
                                    "must be one sym-args here", __file__)
                        if self._is_sym_args_having_nargs(\
                                                argvinfo['new'][arg_ind][0]):
                            kt_obj.insert(obj_ind, (b"n_args", \
                                                        struct.pack('<i', 1)))
                            #Go after n_args
                            obj_ind += 1 

                        # Update the object len to the given in sym-args
                        old_len_ = len(kt_obj[obj_ind][1])
                        new_len_ = argvinfo_new_extracted[arg_ind][0][2] + 1
                        if old_len_ < new_len_:
                            kt_obj[obj_ind] = (kt_obj[obj_ind][0], \
                                                kt_obj[obj_ind][1] + \
                                                b'\0'*(new_len_ - old_len_))
                        else:
                            ERROR_HANDLER.assert_true(old_len_ == new_len_, \
                                    "new arg len lower than pld len (BUG)", \
                                                                    __file__)
                        #Go after argv(arg)
                        obj_ind += 1 
                    else: 
                        #sym-args
                        if self._is_sym_args_having_nargs(\
                                                argvinfo['old'][arg_ind]):
                            ERROR_HANDLER.assert_true(\
                                        kt_obj[obj_ind][0] == b'n_args', \
                                            "must be n_args here", __file__)
                            nargs = struct.unpack('<i', kt_obj[obj_ind][1])[0]
                            old_has_nargs = True
                        else:
                            #n_args == min_n_arg == max_n_arg
                            nargs = int(argvinfo['old'][arg_ind]\
                                                        .strip().split()[1]) 
                            old_has_nargs = False

                        if len(argvinfo['new'][arg_ind]) > 1 \
                                        or argvinfo['old'][arg_ind] \
                                            != argvinfo['new'][arg_ind][0]:
                            # put the args enabled as match to 
                            # the right most in new
                            tmppos_last = obj_ind + nargs 
                            replacement = old2new_cmdargs(\
                                            kt_obj[obj_ind:tmppos_last+1], \
                                            argvinfo_new_extracted[arg_ind], \
                                            old_has_nargs=old_has_nargs)
                            kt_obj[obj_ind:tmppos_last+1] = replacement
                            obj_ind += len(replacement)
                        else:
                            #+1 for n_args obj
                            obj_ind += nargs + int(old_has_nargs) 

            ERROR_HANDLER.assert_true(len(kt_obj) + pointer == obj_ind, \
                                "Some argv objects were not considered? ("\
                                    +str(len(kt_obj))+", "+str(pointer)+", "\
                                                +str(obj_ind)+")", __file__)
    #~ def _updateObjects()

    def _mergeZestiAndKleeKTests (self, outDir, ktestContains_zest, \
                        commonArgs_zest, ktestContains_klee, commonArgs_klee):
        commonArgs = []
        name2ktestMap = {}
        ktestContains = {"CORRESP_TESTNAME":[], "KTEST-OBJ":[]}

        if ktestContains_zest is None:
            ERROR_HANDLER.assert_true(commonArgs_zest is None, "", __file__)
            ERROR_HANDLER.assert_true(ktestContains_klee is not None \
                                and commonArgs_klee is not None, "", __file__)
            ktestContains = ktestContains_klee
            commonArgs = commonArgs_klee
        elif ktestContains_klee is None:
            ERROR_HANDLER.assert_true(commonArgs_klee is None, "", __file__)
            ERROR_HANDLER.assert_true(ktestContains_zest is not None \
                                and commonArgs_zest is not None, "", __file__)
            ktestContains = ktestContains_zest
            commonArgs = commonArgs_zest
        else:
            def getSymArgvParams(symargstr):
                outdict = {}
                tz = symargstr.split()
                if len(tz) == 2: #sym-arg
                    outdict['min'] = outdict['max'] = 1
                    outdict['size'] = int(tz[-1])
                else: #sym-args
                    outdict['min'] = int(tz[-3])
                    outdict['max'] = int(tz[-2])
                    outdict['size'] = int(tz[-1])
                return outdict
            #~ def getSymArgvParams()


            assert commonArgs_zest is not None and commonArgs_klee is not None
            # Common Args must have either sym-arg or sym-args 
            # or sym-files or sym-stdin or sym-stdout
            for common in [commonArgs_zest, commonArgs_klee]:
                for a in common:
                    if "-sym-arg " in a or "-sym-args " in a \
                            or "-sym-files " in a or "-sym-stdin " in a \
                                                        or "-sym-stdout" in a:
                        continue
                    ERROR_HANDLER.error_exit ("Unsupported symbolic "+\
                                "argument: "+a+", in "+str(common), __file__)

            # create merged commonArgs and a map between both zest 
            # and klee commonargs to new commonargs
            argv_zest = {
                    'old':[x for x in commonArgs_zest if "-sym-arg" in x], 
                    'new':[]}
            argv_zest['new'] = [[] for x in argv_zest['old']]
            argv_klee = {
                    'old':[x for x in commonArgs_klee if "-sym-arg" in x], 
                    'new':[]}
            argv_klee['new'] = [[] for x in argv_klee['old']]
            z_ind = 0
            k_ind = 0
            z_cur_inf = None
            k_cur_inf = None
            while True:
                if z_ind < len(argv_zest['old']) \
                                            and k_ind < len(argv_klee['old']):
                    if z_cur_inf is None:
                        z_cur_inf = getSymArgvParams (argv_zest['old'][z_ind])
                    if k_cur_inf is None:
                        k_cur_inf = getSymArgvParams (argv_klee['old'][k_ind])
                    m_min = min(z_cur_inf['min'], k_cur_inf['min'])
                    m_max = min(z_cur_inf['max'], k_cur_inf['max'])
                    M_size = max(z_cur_inf['size'], k_cur_inf['size'])
                    newarg = " ".join(["-sym-args", str(m_min), \
                                                    str(m_max), str(M_size)])

                    # add the new args to each as new, add also to commonArgs
                    commonArgs.append(newarg)
                    argv_zest['new'][z_ind].append(newarg)
                    argv_klee['new'][k_ind].append(newarg)

                    # Update the cur_infs and index
                    if z_cur_inf['max'] == m_max:
                        z_cur_inf = None
                        z_ind += 1
                    else:
                        z_cur_inf['min'] = max(0, z_cur_inf['min'] - m_max)
                        z_cur_inf['max'] = z_cur_inf['max'] - m_max
                    if k_cur_inf['max'] == m_max:
                        k_cur_inf = None
                        k_ind += 1
                    else:
                        k_cur_inf['min'] = max(0, k_cur_inf['min'] - m_max)
                        k_cur_inf['max'] = k_cur_inf['max'] - m_max

                else:
                    # handle inequalities
                    if z_ind < len(argv_zest['old']):
                        argv_klee['old'].append(None)
                        argv_klee['new'].append([])
                        if z_cur_inf is not None:
                            ERROR_HANDLER.assert_true(type(z_cur_inf) == dict,\
                                                "Invalid z_cur_inf", __file__)
                            newarg = " ".join(["-sym-args", \
                                                    str(z_cur_inf['min']), \
                                                    str(z_cur_inf['max']), \
                                                    str(z_cur_inf['size'])])
                            commonArgs.append(newarg)
                            argv_zest['new'][z_ind].append(newarg)
                            argv_klee['new'][k_ind].append(newarg)
                            z_ind += 1
                        #replace sym-arg with sym-args 0 1 because 
                        # not present in other
                        ineqs = [a.replace('sym-arg ', 'sym-args 0 1 ') \
                                        for a in argv_zest['old'][z_ind:]] 
                        commonArgs += ineqs
                        argv_zest['new'][z_ind:] = [[v] for v in ineqs]
                        argv_klee['new'][k_ind] += ineqs
                        break
                    if k_ind < len(argv_klee['old']):
                        argv_zest['old'].append(None)
                        argv_zest['new'].append([])
                        if k_cur_inf is not None:
                            ERROR_HANDLER.assert_true(type(z_cur_inf) == dict,\
                                                "Invalid z_cur_inf", __file__)
                            newarg = " ".join(["-sym-args", \
                                                    str(k_cur_inf['min']), \
                                                    str(k_cur_inf['max']), \
                                                    str(k_cur_inf['size'])])
                            commonArgs.append(newarg)
                            argv_klee['new'][k_ind].append(newarg)
                            argv_zest['new'][z_ind].append(newarg)
                            k_ind += 1
                        # replace sym-arg with sym-args 0 1 because 
                        # not present in other
                        ineqs = [a.replace('sym-arg ', 'sym-args 0 1 ') \
                                        for a in argv_klee['old'][k_ind:]] 
                        commonArgs += ineqs
                        argv_klee['new'][k_ind:] = [[v] for v in ineqs]
                        argv_zest['new'][z_ind] += ineqs
                        break
                    break

            # get sym-stdin, sym-stdout and symfiles
            argv_zest["sym-files"] = {'nFiles-pre':0, 'nFiles':0, 
                                                    'size-pre':0, 'size':0}
            argv_klee["sym-files"] = {'nFiles-pre':0, 'nFiles':0, 
                                                    'size-pre':0, 'size':0}
            argv_zest["sym-std"] = {'in-present-pre': False, 
                                    'in-size-pre':0, 'out-present-pre':False,
                                    'in-present': False, 'in-size':0, 
                                    'out-present':False}
            argv_klee["sym-std"] = {'in-present-pre': False, 'in-size-pre':0,
                                    'out-present-pre':False, 
                                    'in-present': False, 'in-size':0, 
                                    'out-present':False}
            for common, s_argv in [(commonArgs_zest, argv_zest), \
                                            (commonArgs_klee, argv_klee)]:
                # klee considers the last sym-files and stdin so we 
                # just check from begining to end
                for a in common:
                    if '-sym-files ' in a:
                        _, n_f, f_s = a.split()
                        s_argv["sym-files"]["nFiles-pre"] = int(n_f)
                        s_argv["sym-files"]["size-pre"] = int(f_s)
                    elif '-sym-stdin ' in a:
                        s_argv['sym-std']['in-present-pre'] = True
                        s_argv['sym-std']['in-size-pre'] = int(a.split()[-1])
                    elif '-sym-stdout' in a:
                        s_argv['sym-std']['out-present-pre'] = True
            argv_zest['sym-files']['nFiles'] = \
                        argv_klee['sym-files']['nFiles'] = \
                                max(argv_zest['sym-files']['nFiles-pre'], \
                                        argv_klee['sym-files']['nFiles-pre'])
            argv_zest['sym-files']['size'] = \
                            argv_klee['sym-files']['size'] = \
                                max(argv_zest['sym-files']['size-pre'], 
                                        argv_klee['sym-files']['size-pre'])
            argv_zest['sym-std']['in-size'] = \
                            argv_klee['sym-std']['in-size'] = \
                                max(argv_zest['sym-std']['in-size-pre'], \
                                        argv_klee['sym-std']['in-size-pre'])
            argv_zest['sym-std']['in-present'] = \
                        argv_klee['sym-std']['in-present'] = \
                                (argv_zest['sym-std']['in-present-pre'] \
                                    or argv_klee['sym-std']['in-present-pre'])
            argv_zest['sym-std']['out-present'] = \
                        argv_klee['sym-std']['out-present'] = \
                                (argv_zest['sym-std']['out-present-pre'] or \
                                    argv_klee['sym-std']['out-present-pre'])

            if argv_zest['sym-files']['nFiles'] > 0:
                commonArgs.append(" ".join(['-sym-files', \
                            str(argv_zest['sym-files']['nFiles']), \
                                    str(argv_zest['sym-files']['size'])]))
            if argv_zest['sym-std']['in-present']:
                commonArgs.append(" ".join(['-sym-stdin', \
                                    str(argv_zest['sym-std']['in-size'])]))
            if argv_zest['sym-std']['out-present']:
                commonArgs.append("-sym-stdout")

            self._updateObjects (argv_zest, ktestContains_zest)
            self._updateObjects (argv_klee, ktestContains_klee)

            # Merge the two objects
            ktestContains["CORRESP_TESTNAME"] = list(\
                            ktestContains_zest["CORRESP_TESTNAME"] + \
                                    ktestContains_klee["CORRESP_TESTNAME"])
            ktestContains["KTEST-OBJ"] = list(\
                                    ktestContains_zest["KTEST-OBJ"] + \
                                            ktestContains_klee["KTEST-OBJ"])

            # Change the args list in each ktest object with the 
            # common symb args 
            for ktdat in ktestContains["KTEST-OBJ"]:
                ktdat.args = ktdat.args[:1]
                for s in commonArgs:
                    ktdat.args += s.strip().split(' ') 

        # Write the new ktest files
        for i in range(len(ktestContains["CORRESP_TESTNAME"])):
            outFname = os.path.join(outDir, "test"+str(i)+".ktest")
            self._ktestToFile(ktestContains["KTEST-OBJ"][i], outFname)
            name2ktestMap[ktestContains["CORRESP_TESTNAME"][i]] = outFname

        return commonArgs, name2ktestMap
    #~ def _mergeZestiAndKleeKTests ()
#~ class ConvertCollectKtestsSeeds
