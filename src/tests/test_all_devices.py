"""
This tests all requests made by the pyvesync library with pytest.

All tests inherit from the TestBase class which contains the fixtures
and methods needed to run the tests.

The `helpers.call_api` method is patched to return a mock response.
The method, endpoint, headers and json arguments are recorded
in YAML files in the api directory, catagorized in folders by
module and files by the class name.

The default is to record requests that do not exist and compare requests
that already exist. If the API changes, set the overwrite argument to True
in order to overwrite the existing YAML file with the new request.
"""
import logging
from base_test_cases import TestBase
import call_json
import call_json_outlets
import call_json_bulbs
import call_json_fans
import call_json_purifiers
import call_json_humidifiers
import call_json_switches
from utils import assert_test, parse_args

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def test_device_tests():
    """Test to ensure all devices have are defined for testing.

    All devices should have an entry in the DETAILS_RESPONSES dict
    with response for get_details() method. This test ensures that
    all devices have been configured for testing. The details response
    should be located in `{device_type}Details` class of the respective
    call_json_{device_type} module and the DETAILS_RESPONSE module variable.
    The class variable with the details response does not matter, the dictionary
    key of DETAILS_RESPONSES should match the device type.

    Examples
    ---------
    class FanDetails:
        "Core200SResponse": {'speed': 1, 'device_status': 'on'}

    DETAILS_RESPONSES = {
        'Core200S': FanDetails.Core200SResponse
    }

    Asserts
    -------
    Number of devices for each type has a response defined in the
        respective `call_json` module.

    See Also
    --------
    src/tests/README.md - README located in the tests directory
    """
    assert call_json_fans.FANS_NUM == len(call_json_fans.DETAILS_RESPONSES)
    assert call_json_bulbs.BULBS_NUM == len(call_json_bulbs.DETAILS_RESPONSES)
    assert call_json_outlets.OUTLETS_NUM == len(call_json_outlets.DETAILS_RESPONSES)
    assert call_json_switches.SWITCHES_NUM == len(call_json_switches.DETAILS_RESPONSES)
    assert call_json_purifiers.PURIFIERS_NUM == len(call_json_purifiers.DETAILS_RESPONSES)
    assert call_json_humidifiers.HUMIDIFIERS_NUM == len(call_json_humidifiers.DETAILS_RESPONSES)


class TestGeneralAPI(TestBase):
    """General API testing class for login() and get_devices()."""

    def test_get_devices(self):
        """Test get_devices() method request and API response."""
        print("Test Device List")
        self.mock_api.return_value = call_json.DeviceList.device_list_response(), 200
        self.run_in_loop(self.manager.get_devices)
        all_kwargs = parse_args(self.mock_api)
        assert assert_test(self.manager.get_devices, all_kwargs, None,
                           self.write_api, self.overwrite)
        assert len(self.manager.devices.bulbs) == call_json_bulbs.BULBS_NUM
        assert len(self.manager.devices.outlets) == call_json_outlets.OUTLETS_NUM
        assert len(self.manager.devices.fans) == call_json_fans.FANS_NUM
        assert len(self.manager.devices.switches) == call_json_switches.SWITCHES_NUM
