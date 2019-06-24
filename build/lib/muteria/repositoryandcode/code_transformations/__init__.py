
def _make_available():
    import os
    import sys
    import importlib

    import muteria.common.mix as common_mix
    ERROR_HANDLER = common_mix.ErrorHandler
    
    pkg_init_py = os.path.abspath(__file__)
    pkg_path, init_file = os.path.split(pkg_init_py)
    modules_list = []
    # make this pkg visible
    sys.path.insert(0, pkg_path)
    for m in os.listdir(pkg_path):
        # Consider only '.py' files
        if not m.endswith('.py'):
            continue
            
        m_path = os.path.join(os.path.join(pkg_path, m))
        if os.path.isfile(m_path) and m != init_file:
            mod_name = os.path.splitext(m)[0]
            ERROR_HANDLER.assert_true(mod_name not in globals(), \
                    "Invalid module name ({}), change name.".format(mod_name),\
                    __file__)
            ERROR_HANDLER.assert_true('.' not in mod_name, "{} {} {}".format(\
                            "Module name(", mod_name, 
                            ") must not contain dot(.) character"), __file__)
            mod = importlib.import_module(mod_name)

            # Set visible to this package
            globals()[mod_name] = mod
    sys.path.pop(0)
#~ def _make_available()

# Make the different modules visible
_make_available()
del _make_available