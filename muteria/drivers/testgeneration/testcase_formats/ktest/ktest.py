from __future__ import print_function

import os
import re

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
        return True
    #~ def installed()

    @classmethod
    def execute_test(cls, executable_file, test_file, env_vars, timeout=None, \
                                collected_output=None, custom_binary_dir=None):

        prog = cls.tool
        if custom_binary_dir is not None:
            prog = os.path.join(custom_binary_dir, prog)
            ERROR_HANDLER.assert_true(os.path.isfile(prog), \
                            "The tool {} is missing from the specified dir {}"\
                            .format(cls.tool, custom_binary_dir), __file__)

        args = [executable_file, test_file]
        tmp_env = os.environ.copy()
        if env_vars is not None:
            #for e, v in env_vars.items():
            #    tmp_env[e] = v
            tmp_env.update(env_vars)

        timedout_retcodes = (88,) # taken from klee_replay source code
        
        if timeout is not None:
            tmp_env['KLEE_REPLAY_TIMEOUT'] = str(timeout)
        if collected_output is not None:
            retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                prog=prog, args_list=args, env=tmp_env, \
                                                        merge_err_to_out=True)
            out = cls._remove_output_noise(out)
            collected_output.extend(\
                                (retcode, out, (retcode in timedout_retcodes)))
        else:
            retcode, out, err = DriversUtils.execute_and_get_retcode_out_err(\
                                prog=prog, args_list=args, env=tmp_env, \
                                                    out_on=False, err_on=False)

        if retcode in timedout_retcodes + \
                                    (DriversUtils.EXEC_SEGFAULT_OUT_RET_CODE,):
            verdict = common_mix.GlobalConstants.FAIL_TEST_VERDICT
        else:
            verdict = common_mix.GlobalConstants.PASS_TEST_VERDICT

        return verdict
    #~ def execute_test()

    tool = 'klee-replay'

    # Newer version (after klee github commit 88bb205)
    # (88bb205e422ee2aaf75594e4e314b21f77f219e3)
    #clean_everything_regex = re.compile("^KLEE-REPLAY: ")
    #clean_part_regex = re.compile("(" + "|".join(["^KLEE-REPLAY: NOTE: ",\
    #                                    "^KLEE-REPLAY: WARNING: ",\
    #                                    "^KLEE-REPLAY: klee_warning: ",\
    #                                    "^KLEE-REPLAY: klee_warning_once: ",\
    #                                    "^KLEE-REPLAY: klee_assume",\
    #                                    ]))

    # Older version (before klee github commit 88bb205)
    clean_everything_regex = re.compile("(" + "|".join([\
                        "^EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$", \
                        ""+tool+": EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$", \
                        ""+tool+": received signal [0-9]+\\s+. "+\
                                            "Killing monitored process(es)$", \
                        "^note: (pty|pipe) (master|slave): ",\
                        ""+tool+": PTY (MASTER|SLAVE): EXIT STATUS: ", \
                        "^warning: check_file .*: .* "+\
                                    "mismatch: [0-9]+ [vV][sS] [0-9]+$" + ")" \
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
                        ]))
    clean_part_regex = re.compile("(" + "|".join([\
                        "^EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$", \
                        ""+tool+": EXIT STATUS: .* \\([0-9]+\\s+seconds\\)$", \
                        ""+tool+": received signal [0-9]+\\s+. "+\
                                            "Killing monitored process(es)$", \
                        "^note: (pty|pipe) (master|slave): ",\
                        ""+tool+": PTY (MASTER|SLAVE): EXIT STATUS: ", \
                        "^warning: check_file .*: .* "+\
                                    "mismatch: [0-9]+ [vV][sS] [0-9]+$" + ")" \
                        "^RUNNING GDB: /usr/bin/gdb --pid [0-9]+ -q --batch", \
                        "^TIMEOUT: ATTEMPTING GDB EXIT$", \
                        ]))

    @classmethod
    def _remove_output_noise(cls, out, clean_everything=True):
        res = []
        if clean_everything:
            regex = cls.clean_everything_regex
        else:
            regex = cls.clean_part_regex

        if out[-1] == '\n':
            out = out[:-1]
            last_char = "\n" 
        else:
            last_char = ""

        for line in out.splitlines():
            if regex.search(line) is None:
                # None is matched
                res.append(line)
        res = '\n'.join(res) + last_char

        return res
    #~ def _remove_output_noise()

#~ class KTestTestFormat
