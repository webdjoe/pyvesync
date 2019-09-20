import logging
from unittest.mock import patch

import pytest
from pyvesync import VeSync, VeSyncBulbESL100

from . import call_json

DEV_LIST = call_json.DEVLIST_ESL100

DEV_LIST_DETAIL = call_json.LIST_CONF_ESL100

DEVICE_DETAILS = call_json.DETAILS_ESL100


class TestVeSyncBulbESL100:
    """Tests for VeSync dimmable bulb."""

    @pytest.fixture()
    def api_mock(self, caplog):
        """Initilize the mock VeSync class and patch call_api."""
        self.mock_api_call = patch('pyvesync.helpers.Helpers.call_api')
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.vesync_obj = VeSync('sam@mail.com', 'pass')
        self.vesync_obj.enabled = True
        self.vesync_obj.login = True
        self.vesync_obj.token = 'sample_tk'
        self.vesync_obj.account_id = 'sample_actid'
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_esl100_conf(self, api_mock):
        """Tests that Wall Switch is instantiated properly."""
        self.mock_api.return_value = DEV_LIST
        devices = self.vesync_obj.get_devices()
        bulbs = devices[3]
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbESL100)
        assert bulb.device_name == "Etekcity Soft White Bulb"
        assert bulb.device_type == "ESL100"
        assert bulb.cid == "ESL100-CID"
        assert bulb.uuid == "UUID"

    def test_esl100_details(self, api_mock):
        """Test WS get_details()."""
        self.mock_api.return_value = DEVICE_DETAILS
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        bulb.get_details()
        dev_details = bulb.details
        assert bulb.device_status == 'on'
        assert isinstance(dev_details, dict)
        assert bulb.connection_status == 'online'

    def test_esl100_no_details(self, caplog, api_mock):
        """Test no device details for disconnected bulb."""
        self.mock_api.return_value = ({'code': 5}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        bulb.update()
        assert len(caplog.records) == 1

    def test_esl100_onoff(self, caplog, api_mock):
        """Test power toggle for ESL100 bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        assert bulb.turn_off()
        assert bulb.turn_on()

    def test_brightness(self, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        assert bulb.set_brightness(50)

    def test_invalid_brightness(self, caplog, api_mock):
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        assert not bulb.set_brightness(5000)

    def test_features(self, api_mock):
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        assert bulb.dimmable_feature
        assert not bulb.color_temp_feature
        assert not bulb.rgb_shift_feature
