from pyvesync.vesyncoutlet import VeSyncOutlet15A
from pyvesync.helpers import Helpers as helpers
import call_json
import utils
import call_json_outlets

DEVICE_TYPE = 'ESW15-USA'

DEV_LIST_DETAIL = call_json.DeviceList.device_list_item(DEVICE_TYPE)

CORRECT_15A_LIST = call_json.DeviceList.device_list_response(DEVICE_TYPE)

ENERGY_HISTORY = call_json_outlets.ENERGY_HISTORY

CORRECT_15A_DETAILS = call_json_outlets.DETAILS_RESPONSES[DEVICE_TYPE]

BAD_15A_LIST = call_json.DETAILS_BADCODE


class TestVeSyncSwitch(utils.TestBase):

    def test_15aswitch_conf(self):
        """Tests that 15A Outlet is instantiated properly"""
        self.mock_api.return_value = CORRECT_15A_LIST
        self.manager.get_devices()
        outlets = self.manager.outlets
        assert len(outlets) == 1
        vswitch15a = outlets[0]
        assert isinstance(vswitch15a, VeSyncOutlet15A)
        assert vswitch15a.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert vswitch15a.device_type == DEVICE_TYPE
        assert vswitch15a.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert vswitch15a.uuid == call_json.Defaults.uuid(DEVICE_TYPE)

    def test_15a_details(self):
        """Test 15A get_details() """
        self.mock_api.return_value = CORRECT_15A_DETAILS
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        vswitch15a.get_details()
        dev_details = vswitch15a.details
        assert vswitch15a.device_status == 'on'
        assert type(dev_details) == dict
        assert dev_details['active_time'] == 1
        assert dev_details['energy'] == 1
        assert dev_details['power'] == '1'
        assert dev_details['voltage'] == '1'
        assert vswitch15a.power == 1
        assert vswitch15a.voltage == 1
        assert vswitch15a.active_time == 1
        assert vswitch15a.energy_today == 1


class TestVeSync15ASwitch(utils.TestBase):

    def test_15aswitch_conf(self):
        """Tests that 15A Outlet is instantiated properly"""
        self.mock_api.return_value = CORRECT_15A_LIST
        self.manager.get_devices()
        outlets = self.manager.outlets
        assert len(outlets) == 1
        vswitch15a = outlets[0]
        assert isinstance(vswitch15a, VeSyncOutlet15A)
        assert vswitch15a.device_name == call_json.Defaults.name(DEVICE_TYPE)
        assert vswitch15a.device_type == DEVICE_TYPE
        assert vswitch15a.cid == call_json.Defaults.cid(DEVICE_TYPE)
        assert vswitch15a.uuid == call_json.Defaults.uuid(DEVICE_TYPE)

    def test_15a_details_fail(self):
        """Test 15A get_details with Code>0"""
        self.mock_api.return_value = BAD_15A_LIST
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        vswitch15a.get_details()
        assert len(self.caplog.records) == 1
        assert 'details' in self.caplog.text

    def test_15a_no_details(self):
        """Test 15A details return with no details and code=0"""
        bad_15a_details = {'code': 0, 'deviceStatus': 'on'}
        self.mock_api.return_value = bad_15a_details
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        vswitch15a.get_details()
        assert len(self.caplog.records) == 1

    def test_15a_onoff(self):
        """Test 15A Device On/Off Methods"""
        self.mock_api.return_value = {'code': 0}
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        head = helpers.req_headers(self.manager)
        body = helpers.req_body_status(self.manager)

        body['status'] = 'on'
        body['uuid'] = vswitch15a.uuid
        assert vswitch15a.turn_on()
        self.mock_api.assert_called_with(
            '/15a/v1/device/devicestatus', 
            method='put',
            headers=head,
            json_object=body
        )
        assert vswitch15a.turn_off()
        body['status'] = 'off'
        self.mock_api.assert_called_with(
            '/15a/v1/device/devicestatus',
            method='put',
            headers=head,
            json_object=body
        )

    def test_15a_onoff_fail(self):
        """Test 15A On/Off Fail with Code>0"""
        self.mock_api.return_value = {'code': 1}
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        assert not vswitch15a.turn_on()
        assert not vswitch15a.turn_off()

    def test_15a_weekly(self):
        """Test 15A get_weekly_energy"""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        vswitch15a.get_weekly_energy()
        body = helpers.req_body_energy_week(self.manager)
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energyweek',
            method='post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = vswitch15a.energy['week']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.weekly_energy_total == 1

    def test_15a_monthly(self):
        """Test 15A get_monthly_energy"""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        vswitch15a.get_monthly_energy()
        body = helpers.req_body_energy_month(self.manager)
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energymonth',
            method='post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = vswitch15a.energy['month']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.monthly_energy_total == 1

    def test_15a_yearly(self):
        """Test 15A get_yearly_energy"""
        self.mock_api.return_value = ENERGY_HISTORY
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        vswitch15a.get_yearly_energy()
        body = helpers.req_body_energy_year(self.manager)
        body['uuid'] = vswitch15a.uuid
        self.mock_api.assert_called_with(
            '/15a/v1/device/energyyear',
            method='post',
            headers=helpers.req_headers(self.manager),
            json_object=body,
        )
        energy_dict = vswitch15a.energy['year']
        assert energy_dict['energy_consumption_of_today'] == 1
        assert energy_dict['cost_per_kwh'] == 1
        assert energy_dict['max_energy'] == 1
        assert energy_dict['total_energy'] == 1
        assert energy_dict['data'] == [1, 1]
        assert vswitch15a.yearly_energy_total == 1

    def test_history_fail(self):
        """Test 15A energy failure"""
        bad_history = {'code': 1, 'msg': 'FAILLED'}
        self.mock_api.return_value = bad_history
        vswitch15a = VeSyncOutlet15A(DEV_LIST_DETAIL, self.manager)
        vswitch15a.update_energy()
        assert len(self.caplog.records) == 1
        assert 'week' in self.caplog.text
        self.caplog.clear()
        vswitch15a.get_monthly_energy()
        assert len(self.caplog.records) == 1
        assert 'month' in self.caplog.text
        self.caplog.clear()
        vswitch15a.get_yearly_energy()
        assert len(self.caplog.records) == 1
        assert 'year' in self.caplog.text
