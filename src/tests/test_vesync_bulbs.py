import logging
from unittest.mock import MagicMock, patch
from collections import namedtuple
import pytest
from pyvesync import VeSync, VeSyncBulbESL100, VeSyncBulbESL100CW, VeSyncBulbESL100MC, VeSyncBulbValcenoA19MC

from . import call_json

DEV_LIST = call_json.DeviceList.DEVLIST_ESL100

DEV_LIST_DETAIL = call_json.DeviceList.LIST_CONF_ESL100

DEV_LIST_DETAIL_CW = call_json.DeviceList.LIST_CONF_ESL100CW

DEV_LIST_CW = call_json.DeviceList.DEVICE_LIST_RETURN(DEV_LIST_DETAIL_CW)

DEV_LIST_DETAIL_MC = call_json.DeviceList.LIST_CONF_ESL100MC

DEV_LIST_MC = call_json.DeviceList.DEVICE_LIST_RETURN(DEV_LIST_DETAIL_MC)

DEV_LIST_DETAIL_VALCENO = call_json.DeviceList.LIST_CONF_VALCENO

DEV_LIST_VALCENO = call_json.DeviceList.DEVICE_LIST_RETURN(DEV_LIST_DETAIL_VALCENO)

DEVICE_DETAILS = call_json.DETAILS_ESL100

DEVICE_DETAILS_CW = call_json.DETAILS_ESL100CW





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
        self.vesync_obj.get_devices()
        bulbs = self.vesync_obj.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbESL100)
        assert bulb.device_name == 'Etekcity Soft White Bulb'
        assert bulb.device_type == 'ESL100'
        assert bulb.cid == 'ESL100-CID'
        assert bulb.uuid == 'UUID'

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
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100

    def test_features(self, api_mock):
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.vesync_obj)
        assert bulb.dimmable_feature
        assert not bulb.color_temp_feature
        assert not bulb.rgb_shift_feature


class TestVeSyncBulbESL100CW:
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

    def test_esl100cw_conf(self, api_mock):
        """Tests that Wall Switch is instantiated properly."""
        self.mock_api.return_value = DEV_LIST_CW
        self.vesync_obj.get_devices()
        bulbs = self.vesync_obj.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbESL100CW)
        assert bulb.device_name == 'ESL100CW NAME'
        assert bulb.device_type == 'ESL100CW'
        assert bulb.cid == 'ESL100CW-CID'
        assert bulb.uuid == 'ESL100CW-UUID'

    def test_esl100cw_details(self, api_mock):
        """Test WS get_details()."""
        self.mock_api.return_value = DEVICE_DETAILS_CW
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.vesync_obj)
        bulb.get_details()
        assert self.mock_api.r
        assert bulb.device_status == 'on'
        assert bulb.connection_status == 'online'

    def test_esl100cw_onoff(self, caplog, api_mock):
        """Test power toggle for ESL100 bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.vesync_obj)
        assert bulb.turn_off()
        assert bulb.device_status == 'off'
        assert bulb.turn_on()
        assert bulb.device_status == 'on'

    def test_brightness(self, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.vesync_obj)
        assert bulb.set_brightness(50)
        assert bulb.brightness == 50

    def test_invalid_brightness(self, caplog, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.vesync_obj)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100

    def test_color_temp(self, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.vesync_obj)
        assert bulb.set_color_temp(50)
        assert bulb.color_temp_pct == 50

    def test_features(self, api_mock):
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.vesync_obj)
        assert bulb.dimmable_feature
        assert bulb.color_temp_feature
        assert not bulb.rgb_shift_feature

class TestVeSyncBulbESL100MC:
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

    def test_esl100mc_conf(self, api_mock):
        """Tests that Wall Switch is instantiated properly."""
        self.mock_api.return_value = DEV_LIST_MC
        self.vesync_obj.get_devices()
        bulbs = self.vesync_obj.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbESL100MC)
        assert bulb.device_name == 'ESL100MC NAME'
        assert bulb.device_type == 'ESL100MC'
        assert bulb.cid == 'CID-ESL100MC'
        assert bulb.uuid == 'UUID-ESL100MC'

    def test_esl100mc_details(self, api_mock):
        """Test WS get_details()."""
        self.mock_api.return_value = DEV_LIST_MC
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.vesync_obj)
        bulb.get_details()
        assert self.mock_api.r
        assert bulb.device_status == 'on'
        assert bulb.connection_status == 'online'

    def test_esl100mc_onoff(self, caplog, api_mock):
        """Test power toggle for ESL100 bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.vesync_obj)
        assert bulb.turn_off()
        assert bulb.device_status == 'off'
        assert bulb.turn_on()
        assert bulb.device_status == 'on'

    def test_brightness(self, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.vesync_obj)
        assert bulb.set_brightness(50)
        assert bulb.brightness == 50

    def test_invalid_brightness(self, caplog, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.vesync_obj)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100

    def test_color(self, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.vesync_obj)
        assert bulb.set_rgb(50, 100, 150)
        assert bulb.color_rgb == namedtuple('rgb', 'red green blue')(50, 100, 150)

    def test_features(self, api_mock):
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.vesync_obj)
        assert bulb.dimmable_feature
        assert not bulb.color_temp_feature
        assert bulb.rgb_shift_feature

class TestVeSyncBulbValceno:
    """Tests for VeSync Valceno bulb."""

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

    def test_esl100vc_conf(self, api_mock):
        """Tests that Wall Switch is instantiated properly."""
        self.mock_api.return_value = DEV_LIST_VALCENO
        self.vesync_obj.get_devices()
        bulbs = self.vesync_obj.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbValcenoA19MC)
        assert bulb.device_name == 'VALCENO NAME'
        assert bulb.device_type == 'XYD0001'
        assert bulb.cid == 'CID-VALCENO'
        assert bulb.uuid == 'UUID-VALCENO'

    def test_esl100vc_details(self, api_mock):
        """Test WS get_details()."""
        self.mock_api.return_value = DEV_LIST_VALCENO
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.vesync_obj)
        bulb.get_details()
        assert self.mock_api.r
        assert bulb.device_status == 'on'
        assert bulb.connection_status == 'online'

    def test_esl100vc_onoff(self, caplog, api_mock):
        """Test power toggle for ESL100 bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.vesync_obj)
        assert bulb.turn_off()
        assert bulb.device_status == 'off'
        assert bulb.turn_on()
        assert bulb.device_status == 'on'

    def test_brightness(self, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.vesync_obj)
        assert bulb.set_brightness(50)
        assert bulb.brightness == 50

    def test_invalid_brightness(self, caplog, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.vesync_obj)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100

    def test_color(self, api_mock):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.vesync_obj)
        assert bulb.set_rgb(50, 100, 150)
        assert bulb.color_rgb == namedtuple('rgb', 'red green blue')(50, 100, 150)

    def test_features(self, api_mock):
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.vesync_obj)
        assert bulb.dimmable_feature
        assert bulb.color_temp_feature
        assert bulb.rgb_shift_feature