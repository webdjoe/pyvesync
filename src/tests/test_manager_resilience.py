"""Manager and device container failure handling tests.

A device whose class rejects it must be skipped without stopping discovery,
and an unexpected error while updating a device must be logged.
"""

from unittest.mock import AsyncMock, patch

from base_test_cases import TestBase
from call_json import ALL_DEVICE_MAP_DICT, DeviceList

from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


class TestManagerResilience(TestBase):
    """Failure handling in device discovery and update_all_devices()."""

    def test_device_class_error_skips_device_with_warning(self):
        # The CS158 class raises VeSyncError for a config module missing from
        # AIRFRYER_PID_MAP.
        config = DeviceList.device_list_item(ALL_DEVICE_MAP_DICT['CS158-AF'])
        config['configModule'] = 'WiFi_SKA_AirFryer158_XX'
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(config), self.manager
        )
        assert self.manager.devices.air_fryers == []
        assert 'WiFi_SKA_AirFryer158_XX' in self.caplog.text
        other = DeviceList.device_list_item(ALL_DEVICE_MAP_DICT['CAF-DC601S'])
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(other), self.manager
        )
        assert len(self.manager.devices.air_fryers) == 1

    def test_update_all_devices_logs_unexpected_errors(self):
        fryer = self.get_device('air_fryers', 'CAF-DC601S')
        with patch.object(
            type(fryer), 'update', new=AsyncMock(side_effect=RuntimeError('boom'))
        ):
            self.run_in_loop(self.manager.update_all_devices)
        assert 'Unexpected error updating device: boom' in self.caplog.text

    def test_unknown_device_type_is_skipped(self):
        """A device type missing from the device map is skipped, not fatal.

        Regression: the debug log of the unmapped device used an unsupported
        ``to_json(indent=True)`` argument and raised TypeError, which aborted
        ``get_devices()`` for any account with an unrecognised device.
        """
        unknown = ResponseDeviceDetailsModel.from_dict(
            {
                "deviceRegion": "US",
                "isOwner": True,
                "deviceName": "Air Fryer Grill",
                "cid": "unknown-cid",
                "connectionType": "WiFi+BTOnboarding+BTNotify",
                "deviceType": "AG500-CS",
                "type": "SKA",
                "configModule": "WiFiBTOnboardingNotify_Oven_AG500-CS_US",
            }
        )
        assert self.manager.devices._build_device_instance(unknown, self.manager) is None
        self.manager.devices.add_device_from_model(unknown, self.manager)
        assert len(self.manager.devices) == 0
