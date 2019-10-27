import os
import subprocess
import logging

from muteria.drivers import DriversUtils

from muteria.common.mix import GlobalConstants

def make_build_func(repo_root_dir, exe_rel_paths, compiler, flags_list, clean,\
                                                                reconfigure):
    """ Helper for GNU make
    """

    def print_err(out, msg):
        out = out.splitlines()
        #print(out, msg)
        logging.error(str(out), msg)
    #~ def print_err()

    cwd = os.getcwd()
    os.chdir(repo_root_dir)
    
    #try:
    tmp_env = os.environ.copy()
    if compiler is not None:
        tmp_env["CC"] = compiler
    if flags_list is not None:
        tmp_env["CFLAGS"] = " ".join(flags_list)
    
    if reconfigure:
        if os.path.isfile('configure'):
            args_list = ['configure'] 
            retcode, out, _ = DriversUtils.execute_and_get_retcode_out_err(\
                                    prog='bash', args_list=args_list, \
                                    env=tmp_env, merge_err_to_out=True)
        elif os.path.isfile('CMakeLists.txt'):
            args_list = [] 
            retcode, out, _ = DriversUtils.execute_and_get_retcode_out_err(\
                                    prog='cmake', args_list=args_list, \
                                    env=tmp_env, merge_err_to_out=True)
        else:
            retcode = 0
        if retcode != 0:
            print_err(out, "reconfigure failed")
            os.chdir(cwd)
            return GlobalConstants.COMMAND_FAILURE 
        clean = True
    if clean:
        args_list = ['clean']
        retcode, out, _ = DriversUtils.execute_and_get_retcode_out_err(\
                                prog='make', args_list=args_list, \
                                env=tmp_env, merge_err_to_out=True)
        if retcode != 0:
            print_err(out, "clean failed")
            os.chdir(cwd)
            return GlobalConstants.COMMAND_FAILURE 
    
    retcode, out, _ = DriversUtils.execute_and_get_retcode_out_err(\
                        prog='make', env=tmp_env, merge_err_to_out=True)
    if retcode != 0:
        print_err(out, "make")
        os.chdir(cwd)
        return GlobalConstants.COMMAND_FAILURE 
    #except:
    #    os.chdir(cwd)
    #    assert False, "Build Unexpected Error in "+__file__
        #return GlobalConstants.COMMAND_FAILURE

    os.chdir(cwd)
    return GlobalConstants.COMMAND_SUCCESS
#~ def make_build_func()
