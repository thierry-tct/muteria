from __future__ import print_function

import os
import sys
import re
import shutil
import imp
import logging
import filecmp
from distutils.spawn import find_executable

import muteria.common.mix as common_mix

from muteria.drivers import DriversUtils

ERROR_HANDLER = common_mix.ErrorHandler

class KTestTestFormat(object):
    
    @classmethod
    def installed(cls, custom_binary_dir=None):
        """ Check that the tool is installed
            :return: bool reprenting whether the tool is installed or not 
                    (executable accessible on the path)
                    - True: the tool is installed and works
                    - False: the tool is not installed or do not work
        """
        for prog in (cls.tool,):
            if custom_binary_dir is not None:
                prog = os.path.join(custom_binary_dir, prog)
            if not DriversUtils.check_tool(prog=prog, args_list=['--version'],\
                                                    expected_exit_codes=[1]):
                return False
        if not DriversUtils.check_tool(prog=cls.stdbuf, args_list=['--version'],\
                                                    expected_exit_codes=[0]):
                return False
        return True
    #~ def installed()

    @classmethod
    def get_test_replay_tool(cls, custom_replay_tool_binary_dir=None):
        if custom_replay_tool_binary_dir is None:
            kr_file = find_executable(cls.tool)
            ERROR_HANDLER.assert_true(kr_file is not None, \
                        "Could not fine test replay tool on path", __file__)
        else:
            kr_file = os.path.join(custom_replay_tool_binary_dir, cls.tool)
            ERROR_HANDLER.assert_true(os.path.isfile(kr_file), \
                                "replay tool not found in custom_binary_dir", \
                                                                    __file__)
        return kr_file
    #~ def get_test_replay_tool()

    @classmethod
    def _get_replay_prog_args(cls, executable_file, test_file, \
                                        custom_replay_tool_binary_dir=None):
        prog = cls.tool
        if custom_replay_tool_binary_dir is not None:
            prog = os.path.join(custom_replay_tool_binary_dir, prog)
            ERROR_HANDLER.assert_true(os.path.isfile(prog), \
                            "The tool {} is missing from the specified dir {}"\
                            .format(cls.tool, custom_replay_tool_binary_dir), \
                                                                    __file__)

        args = [executable_file, test_file]
        return prog, args
    #~ def _get_replay_prog_args()

    @classmethod
    def execute_test(cls, executable_file, test_file, env_vars, stdin=None, \
                                        must_exist_dir_list=None, \
                                        timeout=None, collected_output=None, \
                                        custom_replay_tool_binary_dir=None):

        prog, args = cls._get_replay_prog_args(executable_file, test_file, \
                                                custom_replay_tool_binary_dir)

        # klee-replay may create files or dir. in KLEE version with LLVM-3.4,
        # those are created in a temporary dir set as <cwd>.temps
        # XXX XXX. make sure each test has its own
        test_work_dir = test_file+".execdir"
        klee_replay_temps = test_work_dir + '.temps'
        for d in (test_work_dir, klee_replay_temps):
            if os.path.isdir(d):
                try:
                    shutil.rmtree(d)
                except PermissionError:
                    cls._dir_chmod777(d)
                    shutil.rmtree(d)
                
        if not os.path.isdir(test_work_dir):
            os.mkdir(test_work_dir)
            
        if must_exist_dir_list is not None:
            for d in must_exist_dir_list:
                td = os.path.join(test_work_dir, d)
                if not os.path.isdir(td):
                    os.makedirs(td)

        # XXX Execution setup
        tmp_env = os.environ.copy()
        if env_vars is not None:
            #for e, v in env_vars.items():
            #    tmp_env[e] = v
            tmp_env.update(env_vars)

        timeout_return_codes = cls.timedout_retcodes + \
                                        DriversUtils.EXEC_TIMED_OUT_RET_CODE

        if timeout is not None:
            tmp_env['KLEE_REPLAY_TIMEOUT'] = str(timeout)
            kt_over = 10 # 1second
            timeout += kt_over
        else:
            # DBG
            logging.warning("@KTEST: calling ktest execution without timeout.")

        # XXX Get the parsing regexes to use
        retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                prog=prog, args_list=['--help'], \
                                merge_err_to_out=True)
        clean_regex, status_regex = cls._get_regexes(out, \
                                                        clean_everything=True)
        
        # XXX Execute the ktest
        #logging.debug("DBG: test_work_dir is {}. its content is {}".format(
        #                    test_work_dir, list(os.listdir(test_work_dir))))
        #if collected_output is not None:
        
        # XXX: Use stdbuf to line buffer the stderr to avoid mixing or 
        # err between klee-replay and the executd prog
        use_stdbuf = True
        if use_stdbuf:
            args = ["--output=L", "--error=L", prog] + args
            prog = "stdbuf"
            # TODO: check that stdbuf is installed
            
        retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                prog=prog, args_list=args, env=tmp_env, \
                                stdin=stdin, \
                                timeout=timeout, timeout_grace_period=5, \
                                merge_err_to_out=True, cwd=test_work_dir)
        retcode, out, exit_status = cls._remove_output_noise(retcode, out, \
                                                  clean_regex, status_regex)
        # In klee-replay, when exit_status here is not None, retcode is 0
        # When there is an issue, like timeout, exit_status is None and
        # retcode has the ode of the issue 
        if exit_status is None:
            exit_status = retcode
        if collected_output is not None:
            collected_output.extend((exit_status, out, \
                                     (retcode in timeout_return_codes or \
                            retcode in DriversUtils.EXEC_TIMED_OUT_RET_CODE)))
        #else:
        #    retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
        #                        prog=prog, args_list=args, env=tmp_env, \
        #                        timeout=timeout, timeout_grace_period=5, \
        #                                        out_on=False, err_on=False, \
        #                                        cwd=test_work_dir)

        # XXX: Go back to previous CWD
        for d in (test_work_dir, klee_replay_temps):
            if os.path.isdir(d):
                try:
                    shutil.rmtree(d)
                except PermissionError:
                    cls._dir_chmod777(d)
                    shutil.rmtree(d)
                
        #if must_exist_dir_list is not None:
        #    try:
        #        shutil.rmtree(test_work_dir)
        #    except PermissionError:
        #        cls._dir_chmod777(test_work_dir)
        #        shutil.rmtree(test_work_dir)

        if retcode in timeout_return_codes + \
                                    DriversUtils.EXEC_SEGFAULT_OUT_RET_CODE:
            verdict = common_mix.GlobalConstants.FAIL_TEST_VERDICT
        else:
            verdict = common_mix.GlobalConstants.PASS_TEST_VERDICT

        return verdict
    #~ def execute_test()

    @staticmethod
    def _dir_chmod777(dirpath):
        try:
            for root_, dirs_, files_ in os.walk(dirpath):
                for sub_d in dirs_:
                    if os.path.isdir(os.path.join(root_, sub_d)):
                        os.chmod(os.path.join(root_, sub_d), 0o777)
                for f_ in files_:
                    if os.path.isfile(os.path.join(root_, f_)):
                        os.chmod(os.path.join(root_, f_), 0o777)
        except PermissionError:
            ret,out,_ = DriversUtils.execute_and_get_retcode_out_err('sudo', \
                                    args_list=['chmod', '777', '-R', dirpath])
            ERROR_HANDLER.assert_true(ret == 0, \
                        "'sudo chmod 777 -R "+dirpath+"' failed (returned "+\
                                        str(ret)+"), error: "+out, __file__)
    #~ def _dir_chmod777()
    
    @classmethod
    def get_replay_test_wrapper_str(cls, exe_env_var, ktest_env_var, \
                                                            timeout_env_var, \
                                        custom_replay_tool_binary_dir=None):
        # XXX: This is used by shadow to replay generated tests through
        # executing base dev test used to generate them.
        # TODO: Let shadow store the mapping between dev test and gen test
        # TODO: Use the mapping to run tests using the returned wrapper by this function
        prog, args = cls._get_replay_prog_args('${}'.format(exe_env_var), \
                                                '${}'.format(ktest_env_var), \
                                               custom_replay_tool_binary_dir)
        
        python_code = ';'.join(['import sys', \
                'from muteria.drivers.testgeneration' \
                    + '.testcase_formats.ktest.ktest import KTestTestFormat', \
            'r, e_s = KTestTestFormat._remove_output_noise(sys.stdin.read())',\
                    'print(r)'])

        bash_timeout_retcode = os.system('timeout 0.1 sleep 1')

        ret_str = "#! /bin/bash\n\n"
        ret_str += "set -u\nset -o pipefail\n\n"
        ret_str += "export KLEE_REPLAY_TIMEOUT={}\n".format(timeout_env_var)
        ret_str += " ".join([prog] + args) + ' 2>&1 | {} -c "{}"\n'.format(\
                                                sys.executable, python_code)
        ret_str += "exit_code=$?\n"
        ret_str += '{} -c "exit(not($exit_code in {}))" && exit_code={}\n'\
                                                .format(sys.executable, \
                                                    cls.timedout_retcodes, \
                                                    bash_timeout_retcode)
        ret_str += "exit $exit_code\n"
        return ret_str
    #~ def get_replay_test_wrapper_str()

    timedout_retcodes = (88,) # taken from klee_replay source code
        
    tool = 'klee-replay'
    stdbuf = 'stdbuf'

    # Newer version (after klee github commit 88bb205)
    # (88bb205e422ee2aaf75594e4e314b21f77f219e3)
    clean_everything_regex_new = re.compile("^KLEE-REPLAY: ")
    clean_part_regex_new = re.compile("(" + "|".join(["^KLEE-REPLAY: NOTE: ",\
                                        "^KLEE-REPLAY: WARNING: ",\
                                        "^KLEE-REPLAY: klee_warning: ",\
                                        "^KLEE-REPLAY: klee_warning_once: ",\
                                        "^KLEE-REPLAY: klee_assume",\
                                        ]) + ")")
    status_regex_new = re.compile(\
                                "^(KLEE-REPLAY: NOTE:\\s+)(EXIT STATUS: .*?)"+\
                                            "(\\s+\\([0-9]+\\s+seconds\\))$")

    # the option "--keep-replay-dir" was added on klee github commit 5b1214a, 
    # right after commit 88bb205
    # So we will use that option to decide whether to use old or new regex
    # Older version (before klee github commit 88bb205)
    clean_everything_regex_old = re.compile("(" + "|".join([\
                        #"^EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$", \
                        #""+tool+": EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$",\
                        ""+tool+": received signal [0-9]+\\s+. "+\
                                        "Killing monitored process\\(es\\)$", \
                        "^note: (pty|pipe) (master|slave): ",\
                        ""+tool+": PTY (MASTER|SLAVE): EXIT STATUS: ", \
                        "^warning: check_file .*: .* "+\
                                        "mismatch: [0-9]+ [vV][sS] [0-9]+$", \
                        "^RUNNING GDB: /usr/bin/gdb --pid [0-9]+ -q --batch", \
                        "^TIMEOUT: ATTEMPTING GDB EXIT$", \
                        #"^ERROR: ", \
                        #"^Error: (executable|chroot:) ", \
                        #"^klee_range(\(|:)", \
                        #"^make_symbolic mismatch, different sizes: ", \
                        #"^WARNING: ", \
                        #"^rootdir: ", \
                        #""+tool+": error: input file ", \
                        ""+tool+": TEST CASE: ", \
                        ""+tool+": ARGS: ", \
                        ]) + ")")
    clean_part_regex_old = re.compile(("(" + "|".join([\
                        #"^EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$", \
                        #""+tool+": EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$", \
                        ""+tool+": received signal [0-9]+\\s+. "+\
                                        "Killing monitored process\\(es\\)$", \
                        "^note: (pty|pipe) (master|slave): ",\
                        ""+tool+": PTY (MASTER|SLAVE): EXIT STATUS: ", \
                        "^warning: check_file .*: .* "+\
                                        "mismatch: [0-9]+ [vV][sS] [0-9]+$", \
                        "^RUNNING GDB: /usr/bin/gdb --pid [0-9]+ -q --batch", \
                        "^TIMEOUT: ATTEMPTING GDB EXIT$", \
                        ]) + ")"))
    status_regex_old = re.compile("^("+tool+\
                    ":\\s+)?(EXIT STATUS: .*?)(\\s+\\([0-9]+\\s+seconds\\))?$")

    @classmethod
    def _get_regexes(cls, out, clean_everything=True):
        if '--keep-replay-dir' in out:
            clean_regex = cls.clean_everything_regex_new if clean_everything \
                                                  else cls.clean_part_regex_new
            status_regex = cls.status_regex_new
        else:
            clean_regex = cls.clean_everything_regex_old if clean_everything \
                                                  else cls.clean_part_regex_old
            status_regex = cls.status_regex_old
        
        return clean_regex, status_regex
    #~ def _get_regexes()
        
    @classmethod
    def _remove_output_noise(cls, retcode, out, clean_regex, status_regex):
        res = []
        
        if len(out) > 0 and out[-1] == '\n':
            out = out[:-1]
            last_char = "\n" 
        else:
            last_char = ""

        # If not None, must be an integer
        exit_status = None

        found_exit_status = False
        for line in out.encode('utf-8', 'backslashreplace').splitlines():
            line = line.decode('utf-8', 'backslashreplace')
            if status_regex.search(line) is not None:
                ERROR_HANDLER.assert_true(not found_exit_status,
                                "Exit status found multiple times in output", \
                                                                      __file__)
                found_exit_status = True
                line = status_regex.sub("\g<2>", line)
                ls = line.split()
                if ls[-2] == 'ABNORMAL':
                    try:
                        exit_status = int(ls[-1])
                    except ValueError:
                        ERROR_HANDLER.error_exit(\
                                    "Invalid exit status {}".format(ls[-1]), \
                                                                 __file__)
                elif ls[-1] == 'OUT' and ls[-2] == 'TIMED':
                    # Case where klee-replay call to gdb fails to attach process
                    if retcode == 0:
                        retcode = cls.timedout_retcodes[0]
                    # klee-replay may pu another exit status
                    found_exit_status = False
                res.append("@MUTERIA.KLEE-REPLAY: "+line)
            elif clean_regex.search(line) is None:
                # None is matched
                res.append(line)

        res = '\n'.join(res) + last_char

        return retcode, res, exit_status
    #~ def _remove_output_noise()

    ktest_extension = '.ktest'
    STDIN_KTEST_DATA_FILE = "muteria-stdin-ktest-data"

    @classmethod
    def ktest_fdupes(cls, *args, custom_replay_tool_binary_dir=None):
        """
        This function computes the fdupes of the klee ktest directories 
        and ktest files given as arguments. 
        It requires that the files and directories passed as arguments exist

        :param *args: each argument is either a file or a directory that exists

        :return: returns two values: 
                - The first is a python list of tuples. 
                    each tuple represents files that are duplicate with each 
                    other and ranked by their age (modified time) the oldest 
                    first (earliest modified to latest modified).
                - The second is the list of files that are not valid
                    ktest files.
        """
        # import ktest
        ktt_dir = os.path.dirname(cls.get_test_replay_tool(
                                        custom_replay_tool_binary_dir=\
                                                custom_replay_tool_binary_dir))
        ktest_tool = imp.load_source("ktest-tool", \
                                        os.path.join(ktt_dir, 'ktest-tool'))

        ret_fdupes = []
        invalid = []
        file_set = set()
        for file_dir in args:
            if os.path.isfile(file_dir):
                file_set.add(file_dir)
            elif os.path.isdir(file_dir):
                # get ktest files recursively
                for root, directories, filenames in os.walk(file_dir):
                    for filename in filenames:
                        if filename.endswith(cls.ktest_extension):
                            file_set.add(os.path.join(root, filename))
            else:
                ERROR_HANDLER.error_exit(\
                        "Invalid file or dir passed (inexistant): "+file_dir, \
                                                                    __file__)

        # apply fdupes: load all ktests and strip the non uniform data 
        # (.bc file used) then compare the remaining data
        kt2used_dat = {}
        kt2stdin = {}
        for kf in file_set:
            try:
                b = ktest_tool.KTest.fromfile(kf)
                if len(b.objects) == 0:
                    invalid.append(kf)
                else:
                    kt2used_dat[kf] = (b.args[1:], b.objects)
            except:
                invalid.append(kf)

            # STDIN
            stdin_file = os.path.join(os.path.dirname(kf), \
                                                    cls.STDIN_KTEST_DATA_FILE)
            if os.path.isfile(stdin_file) \
                                        and os.path.getsize(stdin_file) > 0:
                kt2stdin[kf] = stdin_file
            else:
                kt2stdin[kf] = None

        # do fdupes
        dup_dict = {}
        keys = list(kt2used_dat.keys())
        for ktest_file in keys:
            if ktest_file in kt2used_dat:
                ktest_file_dat = kt2used_dat[ktest_file]
                del kt2used_dat[ktest_file]
                for other_file in kt2used_dat:
                    if kt2used_dat[other_file] == ktest_file_dat:
                        # compare stdin
                        if kt2stdin[ktest_file] == kt2stdin[other_file] or \
                                (kt2stdin[ktest_file] is not None \
                                        and kt2stdin[other_file] is not None \
                                        and filecmp.cmp(kt2stdin[ktest_file], \
                                                        kt2stdin[other_file], 
                                                        shallow=False)):
                            if ktest_file not in dup_dict:
                                dup_dict[ktest_file] = []
                            dup_dict[ktest_file].append(other_file)

                # remove all dupicates from candidates
                if ktest_file in dup_dict:
                    for dup_of_kt_file in dup_dict[ktest_file]:
                        del kt2used_dat[dup_of_kt_file]

        # Finilize
        for ktest_file in dup_dict:
            tmp = [ktest_file] + dup_dict[ktest_file]
            # sort by decreasing modified age
            tmp.sort(key=lambda x: os.path.getmtime(x))
            ret_fdupes.append(tuple(tmp))

        return ret_fdupes, invalid
    #~ def ktest_fdupes()

    @staticmethod
    def get_dir (ktest_fullpath, cand_folders):
        for fold in cand_folders:
            if ktest_fullpath.startswith(fold):
                return fold
        ERROR_HANDLER.error_exit(\
                "Not candidate folder found in {} for ktest {}".format(\
                                cand_folders, ktest_fullpath), __file__)
    #~ def get_dir ()

    @staticmethod
    def cross_tool_fdupes(*testtools):
        clusters = {}
        testdir2ttalias = {}
        for tt in testtools:
            custom_bin = tt.custom_binary_dir
            kt_dir = tt.get_ktests_dir()
            if not os.path.isdir(kt_dir):
                # test generation did not yet take place
                continue
            if custom_bin not in clusters:
                clusters[custom_bin] = []
            clusters[custom_bin].append(kt_dir)
            testdir2ttalias[kt_dir] = tt.config.get_tool_config_alias()

        kepttest2duptest_map = {}
        test2keptdup = {}
        for custom_bin, folders in clusters.items():
            
            tmp_kepttest2duptest_map, tmp_test2keptdup = \
                            KTestTestFormat.cross_folder_fdupes(custom_bin, \
                                                    folders, testdir2ttalias)
            kepttest2duptest_map.update(tmp_kepttest2duptest_map)
            test2keptdup.update(tmp_test2keptdup)
        
        return kepttest2duptest_map, test2keptdup
    #~ def cross_tool_fdupes()

    @staticmethod
    def cross_folder_fdupes(custom_bin, folders, folder2alias):
        dup_list, invalid = KTestTestFormat.ktest_fdupes(*folders, \
                                custom_replay_tool_binary_dir=custom_bin)
        ERROR_HANDLER.assert_true(len(invalid) == 0, \
                            "there should be no invalid here", __file__)

        kepttest2duptest_map= {}
        test2keptdup = {}
        # get fdupes with metatests
        # TODO: check that each result of relpath is really a test
        for dup_tuple in dup_list:
            k_dir = KTestTestFormat.get_dir(dup_tuple[0], folders)
            key = os.path.relpath(dup_tuple[0], k_dir)
            key = DriversUtils.make_meta_element(key, \
                                                    folder2alias[k_dir])
            kepttest2duptest_map[key] = []
            for dp in dup_tuple[1:]:
                v_dir = KTestTestFormat.get_dir(dp, folders)
                val = os.path.relpath(dp, v_dir)
                val = DriversUtils.make_meta_element(val, \
                                                    folder2alias[v_dir])
                kepttest2duptest_map[key].append(val)
                test2keptdup[val] = key
        
        return kepttest2duptest_map, test2keptdup
    #~ def cross_folder_fdupes()
#~ class KTestTestFormat
