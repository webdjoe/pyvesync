"""check_firmware() request and version parsing."""

from base_test_cases import TestBase
from call_json import ALL_DEVICE_MAP_DICT, DeviceList
from defaults import TestDefaults
from utils import parse_args

from pyvesync.const import ConnectionStatus
from pyvesync.models.vesync_models import ResponseDeviceDetailsModel


def _fw_item(cid: str, name: str, versions: list[tuple[str, str, bool]]) -> dict:
    return {
        'deviceCid': cid,
        'deviceName': name,
        'code': 0,
        'msg': None,
        'firmUpdateInfos': [
            {
                'currentVersion': current,
                'latestVersion': current,
                'releaseNotes': '',
                'pluginName': plugin,
                'isMainFw': main,
            }
            for plugin, current, main in versions
        ],
    }


class TestCheckFirmware(TestBase):
    """check_firmware() includes air fryers."""

    def _add(self, setup_entry: str):
        self.manager.devices.add_device_from_model(
            ResponseDeviceDetailsModel.from_dict(
                DeviceList.device_list_item(ALL_DEVICE_MAP_DICT[setup_entry])
            ),
            self.manager,
        )

    def test_air_fryer_in_request_and_version_set(self):
        # Versions from a Core300S (2.0.00) and a CAF-DC111S-AEU
        # getFirmwareUpdateInfoList response 2026-11-07: mcuFw 1.0.10,
        # then mainFw 2.0.02 (isMainFw).
        self.manager.devices.clear()
        self._add('Core300S')
        self._add('CAF-DC111S-AEU')
        purifier = self.manager.devices.air_purifiers[0]
        fryer = self.manager.devices.air_fryers[0]
        self.mock_api.return_value = (
            {
                'traceId': TestDefaults.trace_id,
                'code': 0,
                'msg': 'request success',
                'result': {
                    'cidFwInfoList': [
                        _fw_item(purifier.cid, purifier.device_name, [('mainFw', '2.0.00', True)]),
                        _fw_item(
                            fryer.cid,
                            fryer.device_name,
                            [('mcuFw', '1.0.10', False), ('mainFw', '2.0.02', True)],
                        ),
                    ]
                },
            },
            200,
        )
        assert self.run_in_loop(self.manager.check_firmware)
        sent = parse_args(self.mock_api)['json_object']
        cids = sent.cidList if hasattr(sent, 'cidList') else sent['cidList']
        assert set(cids) == {purifier.cid, fryer.cid}
        assert fryer.current_firm_version == '2.0.02'
        assert purifier.current_firm_version == '2.0.00'

    def test_offline_devices_left_out(self):
        self.manager.devices.clear()
        self._add('Core300S')
        self._add('CAF-DC111S-AEU')
        fryer = self.manager.devices.air_fryers[0]
        fryer.state.connection_status = ConnectionStatus.OFFLINE
        self.mock_api.return_value = (
            {'traceId': TestDefaults.trace_id, 'code': 0, 'msg': '', 'result': {'cidFwInfoList': []}},
            200,
        )
        self.run_in_loop(self.manager.check_firmware)
        sent = parse_args(self.mock_api)['json_object']
        cids = sent.cidList if hasattr(sent, 'cidList') else sent['cidList']
        assert fryer.cid not in cids
