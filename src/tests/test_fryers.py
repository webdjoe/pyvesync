"""Tests for VeSync air fryers."""

from pyvesync.const import ConnectionStatus, DeviceStatus
from pyvesync.device_map import get_air_fryer
from pyvesync.devices.vesynckitchen import VeSyncAirFryer401
from pyvesync.models.vesync_models import ResponseDeviceDetailsModel

from base_test_cases import TestBase


class TestAirFryer401(TestBase):
    """Test CAF-LI401S discovery and status updates."""

    firmware_response = (
        {
            'traceId': 'firmware-trace-id',
            'code': 0,
            'msg': 'request success',
            'result': {
                'cidFwInfoList': [
                    {
                        'deviceCid': 'fryer-cid',
                        'deviceName': 'Kitchen fryer',
                        'code': 0,
                        'msg': None,
                        'firmUpdateInfos': [
                            {
                                'currentVersion': '1.0.13',
                                'latestVersion': '1.0.13',
                                'releaseNotes': 'MCU release notes',
                                'pluginName': 'mcuFw',
                                'isMainFw': False,
                            },
                            {
                                'currentVersion': '2.0.03',
                                'latestVersion': '2.0.03',
                                'releaseNotes': 'Main firmware release notes',
                                'pluginName': 'mainFw',
                                'isMainFw': True,
                            },
                        ],
                    }
                ]
            },
        },
        200,
    )

    @staticmethod
    def _control_response(code: int = 0) -> tuple[dict, int]:
        """Return a bypass V2 control response."""
        return (
            {
                'code': 0,
                'msg': 'request success',
                'result': {'code': code, 'msg': None, 'result': None},
            },
            200,
        )

    @staticmethod
    def _status_response(
        cook_status: str = 'standby',
        *,
        cook_temp: int = 180,
        cook_time: int = 60,
        temp_unit: str = 'c',
    ) -> tuple[dict, int]:
        """Return a bypass V2 status response."""
        steps = []
        if cook_status != 'standby':
            steps.append(
                {
                    'cookSetTime': cook_time,
                    'cookTemp': cook_temp,
                    'mode': 'Custom',
                    'cookLastTime': cook_time,
                    'recipeName': 'Custom',
                    'recipeId': 11,
                    'recipeType': 3,
                }
            )
        return (
            {
                'code': 0,
                'msg': 'request success',
                'result': {
                    'code': 0,
                    'result': {
                        'stepArray': steps,
                        'cookMode': 'normal',
                        'tempUnit': temp_unit,
                        'stepIndex': 0,
                        'cookStatus': cook_status,
                        'preheatSetTime': 0,
                        'preheatLastTime': 0,
                        'preheatEndTime': 0,
                        'preheatTemp': 0,
                        'startTime': 0,
                        'totalTimeRemaining': cook_time,
                        'currentTemp': 25,
                        'shakeStatus': 0,
                    },
                },
            },
            200,
        )

    @staticmethod
    def _details() -> ResponseDeviceDetailsModel:
        return ResponseDeviceDetailsModel.from_dict(
            {
                'deviceRegion': 'EU',
                'isOwner': True,
                'deviceName': 'Kitchen fryer',
                'deviceImg': '',
                'cid': 'fryer-cid',
                'deviceStatus': 'off',
                'connectionStatus': 'online',
                'connectionType': 'WiFi+BTOnboarding+BTNotify',
                'deviceType': 'CAF-LI401S',
                'type': 'SKA',
                'uuid': 'fryer-uuid',
                'configModule': 'VS_WFON_AFR_CAF-LI401S_EU',
                'macID': '',
            }
        )

    def _fryer(self) -> VeSyncAirFryer401:
        feature_map = get_air_fryer('CAF-LI401S')
        assert feature_map is not None
        fryer = VeSyncAirFryer401(self._details(), self.manager, feature_map)
        assert fryer.state.min_temp_c == 75
        assert fryer.state.max_temp_c == 230
        return fryer

    def test_device_map(self) -> None:
        """CAF-LI401S resolves to its V2 fryer class."""
        feature_map = get_air_fryer('CAF-LI401S')
        assert feature_map is not None
        assert feature_map.class_name == 'VeSyncAirFryer401'
        self.manager.devices.add_device_from_model(self._details(), self.manager)
        assert len(self.manager.devices.air_fryers) == 1
        assert isinstance(self.manager.devices.air_fryers[0], VeSyncAirFryer401)

    def test_standby_status(self) -> None:
        """A standby response updates the fryer without cooking state."""
        status_response = (
            {
                'code': 0,
                'msg': 'request success',
                'result': {
                    'code': 0,
                    'result': {
                        'stepArray': [],
                        'cookMode': 'normal',
                        'tempUnit': 'c',
                        'stepIndex': 0,
                        'cookStatus': 'standby',
                        'preheatSetTime': 0,
                        'preheatLastTime': 0,
                        'preheatEndTime': 0,
                        'preheatTemp': 0,
                        'startTime': 0,
                        'totalTimeRemaining': 0,
                        'currentTemp': 58,
                        'shakeStatus': 0,
                    },
                },
            },
            200,
        )
        self.mock_api.return_value = status_response
        fryer = self._fryer()
        self.run_in_loop(fryer.update)

        assert fryer.state.cook_status == 'standby'
        assert fryer.state.temp_unit == 'celsius'
        assert fryer.state.current_temp == 58
        assert fryer.state.device_status == DeviceStatus.OFF
        assert fryer.state.connection_status == ConnectionStatus.ONLINE
        request = self.mock_api.call_args.args[2]
        assert request.payload.method == 'getAirfryerStatus'
        assert request.deviceId == 'fryer-cid'

    def test_standard_firmware_check(self) -> None:
        """The manager firmware API includes air fryers."""
        self.manager.devices.add_device_from_model(self._details(), self.manager)
        fryer = self.manager.devices.air_fryers[0]
        self.mock_api.return_value = self.firmware_response

        assert self.run_in_loop(self.manager.check_firmware) is True

        assert fryer.current_firm_version == '2.0.03'
        assert fryer.latest_firm_version == '2.0.03'
        firmware_call = self.mock_api.call_args
        assert firmware_call.args[0].endswith('/getFirmwareUpdateInfoList')
        assert firmware_call.kwargs['json_object'].cidList == ['fryer-cid']

    def test_cooking_status_converts_seconds_to_minutes(self) -> None:
        """V2 second values are exposed through the legacy minute interface."""
        status_response = (
            {
                'code': 0,
                'msg': 'request success',
                'result': {
                    'code': 0,
                    'result': {
                        'stepArray': [
                            {
                                'cookSetTime': 600,
                                'cookTemp': 200,
                                'mode': 'AirFry',
                                'cookLastTime': 481,
                            }
                        ],
                        'cookMode': 'normal',
                        'tempUnit': 'c',
                        'stepIndex': 0,
                        'cookStatus': 'cooking',
                        'preheatSetTime': 0,
                        'preheatLastTime': 0,
                        'preheatEndTime': 0,
                        'preheatTemp': 0,
                        'startTime': 1,
                        'totalTimeRemaining': 481,
                        'currentTemp': 180,
                        'shakeStatus': 0,
                    },
                },
            },
            200,
        )
        self.mock_api.return_value = status_response
        fryer = self._fryer()
        self.run_in_loop(fryer.update)

        assert fryer.state.cook_status == 'cooking'
        assert fryer.state.cook_set_time == 10
        assert fryer.state.cook_last_time == 9
        assert fryer.state.cook_set_temp == 200
        assert fryer.state.current_temp == 180
        assert fryer.state.temp_unit == 'celsius'
        assert fryer.state.device_status == DeviceStatus.RUNNING

    def test_cook_stages_program_with_physical_start_required(self) -> None:
        """Cook sends the LI401S preset payload and leaves it ready to start."""
        fryer = self._fryer()
        fryer.state.temp_unit = 'celsius'
        fryer.state.cook_status = 'standby'
        self.mock_api.side_effect = [
            self._control_response(),
            self._status_response('ready', cook_temp=180, cook_time=60),
        ]

        assert self.run_in_loop(fryer.cook, 180, 1) is True

        start_request = self.mock_api.call_args_list[0].args[2]
        assert start_request.payload.method == 'startCook'
        assert start_request.payload.data['mode'] == 'Custom'
        assert start_request.payload.data['recipeId'] == 11
        assert start_request.payload.data['readyStart'] is True
        assert start_request.payload.data['tempUnit'] == 'c'
        assert start_request.payload.data['startAct']['cookSetTime'] == 60
        assert start_request.payload.data['startAct']['cookTemp'] == 180
        assert fryer.state.cook_status == 'ready'
        assert fryer.state.cook_mode == 'Custom'
        assert fryer.state.recipe == 'Custom'

    def test_cook_rejects_invalid_settings(self) -> None:
        """Cook rejects values outside the device's documented ranges."""
        fryer = self._fryer()
        fryer.state.temp_unit = 'celsius'
        fryer.state.cook_status = 'standby'

        assert self.run_in_loop(fryer.cook, 74, 10) is False
        assert self.run_in_loop(fryer.cook, 180, 0) is False
        self.mock_api.assert_not_called()

    def test_cook_uses_reported_fahrenheit_unit(self) -> None:
        """US fryers can stage a cook using their reported Fahrenheit unit."""
        fryer = self._fryer()
        fryer.state.temp_unit = 'fahrenheit'
        fryer.state.cook_status = 'standby'
        self.mock_api.side_effect = [
            self._control_response(),
            self._status_response(
                'ready', cook_temp=350, cook_time=60, temp_unit='f'
            ),
        ]

        assert self.run_in_loop(fryer.cook, 350, 1) is True
        request = self.mock_api.call_args_list[0].args[2]
        assert request.payload.data['tempUnit'] == 'f'
        assert request.payload.data['startAct']['cookTemp'] == 350

    def test_cook_checks_inner_device_code(self) -> None:
        """An inner bypass error is not mistaken for a successful command."""
        fryer = self._fryer()
        fryer.state.temp_unit = 'celsius'
        fryer.state.cook_status = 'standby'
        self.mock_api.return_value = self._control_response(11000000)

        assert self.run_in_loop(fryer.cook, 180, 1) is False
        assert self.mock_api.call_count == 1

    def test_end_clears_ready_program(self) -> None:
        """End clears a staged cook and refreshes standby state."""
        fryer = self._fryer()
        fryer.state.temp_unit = 'celsius'
        fryer.state.cook_status = 'ready'
        fryer.state.cook_mode = 'Custom'
        fryer.state.recipe = 'Custom'
        self.mock_api.side_effect = [
            self._control_response(),
            self._status_response(),
        ]

        assert self.run_in_loop(fryer.end) is True

        end_request = self.mock_api.call_args_list[0].args[2]
        assert end_request.payload.method == 'endCook'
        assert fryer.state.cook_status == 'standby'
        assert fryer.state.cook_mode is None
        assert fryer.state.recipe is None

    def test_set_cook_time_updates_active_cook(self) -> None:
        """The remaining cook time can be changed while actively cooking."""
        fryer = self._fryer()
        fryer.state.temp_unit = 'celsius'
        fryer.state.cook_status = 'cooking'
        self.mock_api.side_effect = [
            self._control_response(),
            self._status_response('cooking', cook_temp=75, cook_time=120),
        ]

        assert self.run_in_loop(fryer.set_cook_time, 2) is True

        set_time_request = self.mock_api.call_args_list[0].args[2]
        assert set_time_request.payload.method == 'setTimeOrTemp'
        assert set_time_request.payload.data == {
            'cookSetTime': 120,
            'hasLinkage': False,
        }
        assert fryer.state.cook_set_time == 2
        assert fryer.state.cook_last_time == 2

    def test_set_cook_time_rejects_invalid_time(self) -> None:
        """Cook time adjustment uses the device's one-to-sixty-minute range."""
        fryer = self._fryer()
        fryer.state.cook_status = 'cooking'

        assert self.run_in_loop(fryer.set_cook_time, 0) is False
        assert self.run_in_loop(fryer.set_cook_time, 61) is False
        self.mock_api.assert_not_called()

    def test_set_cook_time_requires_active_cook(self) -> None:
        """The device only accepts time adjustment while actively cooking."""
        fryer = self._fryer()
        fryer.state.cook_status = 'standby'
        self.mock_api.return_value = self._status_response()

        assert self.run_in_loop(fryer.set_cook_time, 2) is False
        assert self.mock_api.call_count == 1
        request = self.mock_api.call_args.args[2]
        assert request.payload.method == 'getAirfryerStatus'
