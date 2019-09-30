
from __future__ import print_function

import os
import muteria.common.fs as common_fs
import muteria.common.mix as common_mix

ERROR_HANDLER = common_mix.ErrorHandler

class TestOracleManager(object):
    """ This class represent the test oracle manager
    """

    METADATA_FILE = ".test_oracle_mgr.metadata"

    def __init__(self, config):
        self.config = config

        # Initialize data based on config (TODO)

        self.object_to_dir = {}

        self.set_oracle()
    #~ def __init__()

    def oracle_checks_output(self):
        # TODO
        return True
    #~ def _oracle_checks_output()

    def _is_valid_metadata(self, oracles_dir):
        m_data = os.path.join(oracles_dir, self.METADATA_FILE)
        if not os.path.isfile(m_data):
            return False
        with open(m_data) as f:
            if f.read().strip() != os.path.abspath(oracles_dir):
                return False
        return True
    #~ def _is_valid_metadata()

    def _update_metadata(self, oracles_dir):
        # TODO: invalidate the saved oracles

        m_data = os.path.join(oracles_dir, self.METADATA_FILE)
        with open(m_data, 'w') as f:
            f.write(os.path.abspath(oracles_dir))
    #~ def _update_metadata()

    def add_mapping(self, tool_object, oracles_dir):
        ERROR_HANDLER.assert_true(tool_object not in self.object_to_dir, \
                "tool_object is already present with oracle dir: "+oracles_dir)
        self.object_to_dir[tool_object] = oracles_dir

        if self.oracle_checks_output():
            if not os.path.isdir(oracles_dir):
                os.mkdir(oracles_dir)
            if not self._is_valid_metadata(oracles_dir):
                self._update_metadata(oracles_dir)
    #~ def add_mapping()

    def set_oracle(self, passfail=False, criteria_on=None):
        self.passfail = passfail
        self.criteria_on = criteria_on
    #~ def set_oracle()
#~ class TestOracleManager