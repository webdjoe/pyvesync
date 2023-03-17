from collections import namedtuple
from pyvesync.helpers import RGB
from pyvesync.vesyncbulb import (VeSyncBulbESL100, VeSyncBulbESL100CW,
                                 VeSyncBulbESL100MC, VeSyncBulbValcenoA19MC)
import call_json
import call_json_bulbs
from utils import TestBase

DEV_LIST = call_json.DeviceList.device_list_response('ESL100')

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item('ESL100')

DEV_LIST_DETAIL_CW = call_json.DeviceList.device_list_item('ESL100CW')

DEV_LIST_CW = call_json.DeviceList.device_list_response('ESL100CW')

DEV_LIST_DETAIL_MC = call_json.DeviceList.device_list_item('ESL100MC')

DEV_LIST_MC = call_json.DeviceList.device_list_response('ESL100MC')

DEV_LIST_DETAIL_VALCENO = call_json.DeviceList.device_list_item('XYD0001')

DEV_LIST_VALCENO = call_json.DeviceList.device_list_response('XYD0001')

DEVICE_DETAILS = call_json_bulbs.DETAILS_RESPONSES['ESL100']

DEVICE_DETAILS_CW = call_json_bulbs.DETAILS_RESPONSES['ESL100CW']

DEFAULTS = call_json.Defaults


class TestVeSyncBulbESL100(TestBase):
    """Tests for VeSync dimmable bulb."""
    device_type = 'ESL100'

    def test_esl100_conf(self):
        """Tests that Wall Switch is instantiated properly."""
        self.mock_api.return_value = DEV_LIST
        self.manager.get_devices()
        bulbs = self.manager.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbESL100)
        assert bulb.device_name == call_json.Defaults.name(self.device_type)
        assert bulb.device_type == self.device_type
        assert bulb.cid == call_json.Defaults.cid(self.device_type)
        assert bulb.uuid == call_json.Defaults.uuid(self.device_type)

    def test_esl100_details(self):
        """Test WS get_details()."""
        if callable(DEVICE_DETAILS):
            self.mock_api.return_value = DEVICE_DETAILS()
        else:
            self.mock_api.return_value = DEVICE_DETAILS
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.manager)
        bulb.get_details()
        dev_details = bulb.details
        assert bulb.device_status == 'on'
        assert isinstance(dev_details, dict)
        assert bulb.connection_status == 'online'

    def test_esl100_no_details(self):
        """Test no device details for disconnected bulb."""
        self.mock_api.return_value = ({'code': 5}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.manager)
        bulb.update()
        assert len(self.caplog.records) == 1

    def test_esl100_onoff(self):
        """Test power toggle for ESL100 bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.manager)
        assert bulb.turn_off()
        assert bulb.turn_on()

    def test_brightness(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.manager)
        assert bulb.set_brightness(50)

    def test_invalid_brightness(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.manager)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100

    def test_features(self):
        bulb = VeSyncBulbESL100(DEV_LIST_DETAIL, self.manager)
        assert bulb.dimmable_feature
        assert not bulb.color_temp_feature
        assert not bulb.rgb_shift_feature


class TestVeSyncBulbESL100CW(TestBase):
    """Tests for VeSync dimmable bulb."""
    device_type = 'ESL100CW'

    def test_esl100cw_conf(self):
        """Tests that Wall Switch is instantiated properly."""
        if callable(DEV_LIST_CW):
            self.mock_api.return_value = DEV_LIST_CW()
        else:
            self.mock_api.return_value = DEV_LIST_CW
        self.manager.get_devices()
        bulbs = self.manager.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbESL100CW)
        assert bulb.device_name == DEFAULTS.name(self.device_type)
        assert bulb.device_type == self.device_type
        assert bulb.cid == DEFAULTS.cid(self.device_type)
        assert bulb.uuid == DEFAULTS.uuid(self.device_type)

    def test_esl100cw_details(self):
        """Test WS get_details()."""
        if callable(DEVICE_DETAILS_CW):
            self.mock_api.return_value = DEVICE_DETAILS_CW()
        else:
            self.mock_api.return_value = DEVICE_DETAILS_CW
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.manager)
        bulb.get_details()
        assert self.mock_api.r
        assert bulb.device_status == 'on'
        assert bulb.connection_status == 'online'

    def test_esl100cw_onoff(self):
        """Test power toggle for ESL100 bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.manager)
        assert bulb.turn_off()
        assert bulb.device_status == 'off'
        assert bulb.turn_on()
        assert bulb.device_status == 'on'

    def test_brightness(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.manager)
        assert bulb.set_brightness(50)
        assert bulb.brightness == 50

    def test_invalid_brightness(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.manager)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100

    def test_color_temp(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.manager)
        assert bulb.set_color_temp(50)
        assert bulb.color_temp_pct == 50

    def test_features(self):
        bulb = VeSyncBulbESL100CW(DEV_LIST_DETAIL_CW, self.manager)
        assert bulb.dimmable_feature
        assert bulb.color_temp_feature
        assert not bulb.rgb_shift_feature


class TestVeSyncBulbESL100MC(TestBase):
    """Tests for VeSync dimmable bulb."""
    device_type = 'ESL100MC'

    def test_esl100mc_conf(self):
        """Tests that Wall Switch is instantiated properly."""
        self.mock_api.return_value = DEV_LIST_MC
        self.manager.get_devices()
        bulbs = self.manager.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbESL100MC)
        assert bulb.device_name == DEFAULTS.name(self.device_type)
        assert bulb.device_type == self.device_type
        assert bulb.cid == DEFAULTS.cid(self.device_type)
        assert bulb.uuid == DEFAULTS.uuid(self.device_type)

    def test_esl100mc_details(self):
        """Test WS get_details()."""
        self.mock_api.return_value = DEV_LIST_MC
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.manager)
        bulb.get_details()
        assert self.mock_api.r
        assert bulb.device_status == 'on'
        assert bulb.connection_status == 'online'

    def test_esl100mc_onoff(self):
        """Test power toggle for ESL100 bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.manager)
        assert bulb.turn_off()
        assert bulb.device_status == 'off'
        assert bulb.turn_on()
        assert bulb.device_status == 'on'

    def test_brightness(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.manager)
        assert bulb.set_brightness(50)
        assert bulb.brightness == 50

    def test_invalid_brightness(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.manager)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100

    def test_color(self):
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.manager)
        assert bulb.set_rgb(50, 100, 150)
        assert bulb.color_rgb == namedtuple('rgb', 'red green blue')(50, 100, 150)

    def test_features(self):
        bulb = VeSyncBulbESL100MC(DEV_LIST_DETAIL_MC, self.manager)
        assert bulb.dimmable_feature
        assert not bulb.color_temp_feature
        assert bulb.rgb_shift_feature


class TestVeSyncBulbValceno(TestBase):
    """Tests for VeSync Valceno bulb."""
    device_type = 'XYD0001'

    def test_valceno_conf(self):
        """Tests that Valceno is instantiated properly."""
        self.mock_api.return_value = DEV_LIST_VALCENO
        self.manager.get_devices()
        bulbs = self.manager.bulbs
        assert len(bulbs) == 1
        bulb = bulbs[0]
        assert isinstance(bulb, VeSyncBulbValcenoA19MC)
        assert bulb.device_name == DEFAULTS.name(self.device_type)
        assert bulb.device_type == self.device_type
        assert bulb.cid == DEFAULTS.cid(self.device_type)
        assert bulb.uuid == DEFAULTS.uuid(self.device_type)

    def test_valceno_details(self):
        """Test Valceno get_details()."""
        self.mock_api.return_value = DEV_LIST_VALCENO
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        bulb.get_details()
        assert self.mock_api.r
        assert bulb.device_status == 'on'
        assert bulb.connection_status == 'online'

    def test_valceno_onoff(self):
        """Test power toggle for Valceno MC bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        assert bulb.turn_off()
        assert bulb.device_status == 'off'
        assert bulb.turn_on()
        assert bulb.device_status == 'on'

    def test_brightness(self):
        """Test brightness on Valceno."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        assert bulb.set_brightness(50)
        assert bulb.brightness == 50

    def test_invalid_brightness(self):
        """Test invalid brightness on Valceno."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        assert bulb.set_brightness(5000)
        assert bulb.brightness == 100
        
    def test_invalid_saturation(self):
        """Test invalid saturation on Valceno."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        assert bulb.set_color_saturation(5000)
        body_dict = {
            "method": "setLightStatusV2",
            "source": "APP",
            "data":
                {
                    "force": 1,
                    "brightness": "",
                    "colorTemp": "",
                    "colorMode": "hsv",
                    "hue": "",
                    "saturation": 10000,
                    "value": ""
                }
        }
        mock_call = self.mock_api.call_args[1]['json_object']['payload']
        assert mock_call == body_dict

    def test_color(self):
        """Test set color on Valceno."""
        self.mock_api.return_value = ({
            'code': 0,
            'msg': '',
            'result': {
                'code': 0,
                'result': {
                    "enabled": 'on',
                    "colorMode": 'hsv',
                    'brightness': 100,
                    'hue': 5833,
                    'saturation': 6700,
                    'value': 59
                }
            }
        }, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        assert bulb.set_rgb(50, 100, 150)
        assert bulb.color_rgb == RGB(50, 100, 150)

    def test_hue(self):
        """Test hue on Valceno MC Bulb."""
        self.mock_api.return_value = ({'code': 0}, 200)
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        bulb.set_color_hue(230.5)
        body_dict = {
            "method": "setLightStatusV2",
            "source": "APP",
            "data":
                {
                    "force": 1,
                    "brightness": "",
                    "colorTemp": "",
                    "colorMode": "hsv",
                    "hue": 6403,
                    "saturation": "",
                    "value": ""
                }
        }
        mock_call = self.mock_api.call_args[1]['json_object']['payload']
        assert mock_call == body_dict

    def test_features(self):
        bulb = VeSyncBulbValcenoA19MC(DEV_LIST_DETAIL_VALCENO, self.manager)
        assert bulb.dimmable_feature
        assert bulb.color_temp_feature
        assert bulb.rgb_shift_feature
