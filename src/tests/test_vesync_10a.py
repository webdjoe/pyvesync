import pytest
from unittest.mock import patch
import logging
from pyvesync import VeSync, VeSyncOutlet10A
import pyvesync
from pyvesync.helpers import Helpers as helpers


class Test10AOutlet:
    @pytest.fixture
    def api_mock(self, caplog):
        self.mock_api_call = patch.object(pyvesync.helpers.Helpers, 'call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.login = True
        self.vesync_obj.tk = 'sample_tk'
        self.vesync_obj.account_id = 'sample_actid'
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()