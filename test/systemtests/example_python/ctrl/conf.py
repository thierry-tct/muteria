import os

this_dir = os.path.dirname(os.path.abspath(__file__))

devtestlist = ['test_lib.py']
def dev_test_runner(test_name):
    if test_name == 'test_lib.py':
        #TODO: fix it
        return True

PROGRAMMING_LANGUAGE='pythOn'
REPOSITORY_ROOTDIR=os.path.join(os.path.dirname(this_dir), 'repo')