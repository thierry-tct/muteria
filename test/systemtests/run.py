
import os
import sys

assert len(sys.argv) == 3, "expects 2 args: <muteria root dir> <proj conf dir>"
m_root = os.path.abspath(sys.argv[1])
proj_conf_dir = os.path.abspath(sys.argv[2])
sys.path.insert(0, m_root)

import muteria.controller.main_controller as m_ctrl
import muteria.configmanager.helper as cfg_helper

thisdir = os.path.dirname(os.path.abspath(__file__))
conf_file = os.path.join(proj_conf_dir, 'conf.py')
lang = 'python'

# load config
cfg_obj = cfg_helper.ConfigurationHelper()
raw_conf = cfg_obj.get_extend_file_raw_conf(conf_file, lang)

# Compute
ctrl = m_ctrl.MainController()
ctrl.raw_config_main(raw_conf)

print("# Done <run.py>")