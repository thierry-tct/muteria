import muteria.common.mix as common_mix
import muteria.common.fs as common_fs

ERROR_HANDLER = common_mix.ErrorHandler

class TestToolType(common_mix.EnumAutoName):
    USE_ONLY_CODE = "StaticTestcaseTool"
    USE_ONLY_MUTANT_CODE = "StaticMutantTestcaseTool"
    USE_CODE_AND_TESTS = "DynamicTestcaseTool"
    USE_MUTANT_CODE_AND_TESTS = "DynamicMutantTestcaseTool"

    def get_tool_type_classname(self):
        return self.get_field_value()
    #~ def get_tool_type_classname():
#~ class TestToolType

class RepoFileToCustomMap(dict):
    """ This class define a mapping between a repository file and its 
    custom coresponding file. This is usefule to let the testcase tool
    know which file to replace during test execution.
    Just specify the files to change. If none is specified, the default 
    files in the repository are used.
    """

    def __init__(self):
        pass
    #~ def __init__()

    def add_map(self, repo_val, custom_val):
        ERROR_HANDLER.assert_true(repo_val not in self, \
                        "adding map failed: key {} already present.".format( \
                            repo_val), __file__)
        self[repo_val] = custom_val
    #~ def add_map()

    def update_custom_value(self, repo_val, custom_val):
        ERROR_HANDLER.assert_true(repo_val in self, \
                        "updating map failed: key {} not present.".format( \
                            repo_val), __file__)
        self[repo_val] = custom_val
    #~ def update_custom_value()

    def delete_map(self, repo_val):
        ERROR_HANDLER.assert_true(repo_val in self, \
                        "deleting map failed: key {} not present.".format( \
                            repo_val), __file__)
        del self[repo_val]
    #~ def get_custom_value()

    def get_custom_value(self, repo_val):
        ERROR_HANDLER.assert_true(repo_val in self, \
                        "getting map failed: key {} not present.".format( \
                            repo_val), __file__)
        return self[repo_val]
    #~ def get_custom_value()

    def write_to_file(self, filepath):
        common_fs.dumpJSON(self, filepath)
    #~ def write_to_file()

    def read_from_file(self, filepath):
        obj = common_fs.loadJSON(self, filepath)
        for k in obj:
            self.add_map(k, obj[k])
    #~ def write_to_file()
        
#~ class RepoFileToCustomMap