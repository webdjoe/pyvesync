"""Levoit Air Purifier tests."""
import orjson
from pyvesync.devices.vesyncpurifier import VeSyncAirBypass
from pyvesync.devices.vesyncpurifier import VeSyncAir131
from pyvesync.utils.helpers import Helpers as Helpers
import call_json
import call_json_fans
from base_test_cases import TestBase
from defaults import Defaults

LVPUR131S = 'LV-PUR131S'
CORE200S = 'Core200S'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(LVPUR131S)
CORE200S_DETAIL = call_json.DeviceList.device_list_item(CORE200S)

CORRECT_LIST = call_json.DeviceList.device_list_response(LVPUR131S)

CORRECT_DETAILS = call_json_fans.DETAILS_RESPONSES[LVPUR131S]

BAD_LIST = call_json.DETAILS_BADCODE


class TestVesyncAirPurifier(TestBase):
    """Air purifier tests."""

    def test_airpur_conf(self):
        """Tests that 15A Outlet is instantiated properly."""
        self.mock_api.return_value = CORRECT_LIST
        self.run_in_loop(self.manager.get_devices)
        fans = self.manager.fans
        assert len(fans) == 1
        fan = fans[0]
        assert isinstance(fan, VeSyncAir131)
        assert fan.device_name == Defaults.name(LVPUR131S)
        assert fan.device_type == LVPUR131S
        assert fan.cid == Defaults.cid(LVPUR131S)
        assert fan.uuid == Defaults.uuid(LVPUR131S)

    def test_airpur_details(self):
        """Test Air Purifier get_details()."""
        resp_dict, status = CORRECT_DETAILS
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(fan.get_details)
        dev_details = fan.details
        assert fan.device_status == 'on'
        assert isinstance(dev_details, dict)
        assert dev_details['active_time'] == 1
        assert fan.filter_life == call_json_fans.FanDefaults.filter_life
        assert dev_details['screen_status'] == Defaults.str_toggle
        assert fan.mode == 'manual'
        assert dev_details['level'] == call_json_fans.FanDefaults.fan_level
        assert fan.fan_level == call_json_fans.FanDefaults.fan_level
        assert dev_details['air_quality'] == 'excellent'
        assert fan.air_quality == 'excellent'

    def test_airpur_details_fail(self):
        """Test Air Purifier get_details with Code>0."""
        resp_dict, status = BAD_LIST
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.manager)
        self.run_in_loop(fan.get_details)
        assert len(self.caplog.records) == 1
        assert 'details' in self.caplog.text

    def test_airpur_onoff(self):
        """Test Air Purifier Device On/Off Methods."""
        self.mock_api.return_value = (orjson.dumps({'code': 0}), 200)
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.manager)
        head = Helpers.req_legacy_headers(self.manager)
        body = Helpers.req_body(self.manager, 'devicestatus')
        fan.device_status = 'off'
        body['status'] = 'on'
        body['uuid'] = fan.uuid
        on = self.run_in_loop(fan.turn_on)
        self.mock_api.assert_called_with(
            '/131airPurifier/v1/device/deviceStatus', 'put',
            json_object=body, headers=head)
        call_args = self.mock_api.call_args_list[0][0]
        assert call_args[0] == '/131airPurifier/v1/device/deviceStatus'
        assert call_args[1] == 'put'
        assert on
        fan.device_status = 'on'
        off = self.run_in_loop(fan.turn_off)
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/131airPurifier/v1/device/deviceStatus', 'put',
            json_object=body, headers=head)
        assert off

    def test_airpur_onoff_fail(self):
        """Test Air Purifier On/Off Fail with Code>0."""
        self.mock_api.return_value = (orjson.dumps({'code': 1}), 400)
        vsfan = VeSyncAir131(DEV_LIST_DETAIL, self.manager)
        assert not self.run_in_loop(vsfan.turn_on)
        assert not self.run_in_loop(vsfan.turn_off)

    def test_airpur_fanspeed(self):
        """Test changing fan speed of."""
        self.mock_api.return_value = (orjson.dumps({'code': 0}), 200)
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.manager)
        fan.mode = 'manual'
        fan.details['level'] = 1
        b = self.run_in_loop(fan.set_fan_speed)
        assert fan.fan_level == 2
        b = self.run_in_loop(fan.set_fan_speed)
        assert fan.fan_level == 3
        b = self.run_in_loop(fan.set_fan_speed)
        assert fan.fan_level == 1
        assert b
        b = self.run_in_loop(fan.set_fan_speed, 2)
        assert b
        assert fan.fan_level == 2

    def test_mode_toggle(self):
        """Test changing modes on air purifier."""
        self.mock_api.return_value = (orjson.dumps({'code': 0}), 200)
        fan = VeSyncAir131(DEV_LIST_DETAIL, self.manager)
        f = self.run_in_loop(fan.auto_mode)
        assert f
        assert fan.mode == 'auto'
        f = self.run_in_loop(fan.manual_mode)
        assert fan.mode == 'manual'
        assert f
        f = self.run_in_loop(fan.sleep_mode)
        assert fan.mode == 'sleep'
        assert f

    def test_airpur_set_timer(self):
        """Test timer function of Core*00S Purifiers."""
        self.mock_api.return_value = (
            orjson.dumps(call_json_fans.INNER_RESULT({'id': 1})), 200
            )
        fan = VeSyncAirBypass(CORE200S_DETAIL, self.manager)
        self.run_in_loop(fan.set_timer, 100)
        assert fan.timer is not None
        assert fan.timer.timer_duration == 100
        assert fan.timer.done is False
        assert fan.timer.action == 'off'
        assert fan.timer.running is True

    def test_airpur_clear_timer(self):
        """Test clear_timer method for Core air purifiers."""
        resp_dict, status = call_json_fans.FunctionResponses['Core200S']
        self.mock_api.return_value = orjson.dumps(resp_dict), status
        fan = VeSyncAirBypass(CORE200S_DETAIL, self.manager)
        fan.timer = call_json_fans.FAN_TIMER
        self.run_in_loop(fan.clear_timer)
        assert fan.timer is None
