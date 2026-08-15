# The pyvesync testing library

This is the testing suite for the pyvesync library. Each device that is added must include tests. This helps to maintain the consistency of the API as new devices are added and the backend is refactored.

I've built a relatively simple framework to ease the burden of writing tests. There are some old tests that I had previously written that I've kept as I build the new framework but these tests were not comprehensive or portable. The files that begin with `xtest_x_` are these previous tests - pytest does not collect them (the filename does not start with `test`) and they can safely be ignored.

> **Note:** the files named `test_x_vesync_login.py` and `test_x_vesync_api_responses.py` are **not** legacy. They are current tests for the login flow and low-level `async_call_api()` error handling. Only the `xtest_x_*` files are legacy.

The tests primarily run each API call for each device and record the request details in YAML files in the `src/tests/api` directory. These files are then used to verify the request when the test is run again.

## Two testing layers

The suite verifies devices at two different levels, both defined in `base_test_cases.py`:

- **`TestBase` (the common case)** - patches `VeSync.async_call_api()`. The mock intercepts each device method *before* any HTTP request is made, capturing the URL, method, headers and JSON body so they can be compared against the recorded YAML fixtures. This is what every `test_<device_type>.py` module uses.
- **`TestApiFunc`** - patches `aiohttp.ClientSession` directly and drives the full HTTP request/response cycle using `AiohttpMockSession` from `aiohttp_mocker.py`. It is used for login tests and for exercising `async_call_api()` error handling (rate limits, server errors, non-200 status codes).

Both base classes expose `self.manager` (a logged-in `VeSync` instance), `self.mock_api`, `self.caplog`, and a `run_in_loop()` helper for running coroutines synchronously. `TestBase` additionally provides `get_device(product_type, setup_entry)` to instantiate a single device for a test.

## Framework structure

The structure of the framework is as follows:

1. `call_json.py` - This file contains general functions and the device list builder. This file does not need to be edited when adding a device.
2. `call_json_DEVICE.py` - This file contains device specific responses such as the `get_details()` response and specific method responses. This file pulls in the device type list from `device_map.*_modules`. The minimum addition is to add the appropriate `get_details()` response to the `DETAILS_RESPONSES` dictionary keyed by setup entry.
3. `test_DEVICE.py` - Each device module in pyvesync has its own test module, typically with one class that inherits the `base_test_cases.TestBase` class. The class has two test methods - `test_details()` and `test_methods()` - that are parametrized by `conftest.pytest_generate_tests`.
4. `base_test_cases.py` - Contains the `TestBase` class (fixture that instantiates the `VeSync` object and patches the `async_call_api()` method) and the `TestApiFunc` class (patches `aiohttp.ClientSession` directly for full request/response cycle tests).
5. `defaults.py` - Contains the general default values for all devices in the `TestDefaults` class, the `FunctionResponses`/`FunctionResponsesV1`/`FunctionResponsesV2` response factories and the `build_bypass_v1_response()`/`build_bypass_v2_response()` helpers.
6. `utils.py` - Contains the YAML fixture reader/writer (`YAMLWriter`), `parse_args()` (extracts the mocked call arguments), `assert_test()` (compares or writes YAML) and `api_scrub()` (normalizes sensitive data).
7. `conftest.py` - Contains the `pytest_generate_tests` function that is used to parametrize the tests based on all device types listed in the respective modules, plus the `--write_api`/`--overwrite` command line options.

### Full file reference

| File | Purpose |
| ---- | ------- |
| `base_test_cases.py` | `TestBase` (patches `async_call_api`) and `TestApiFunc` (patches `ClientSession`). See [Two testing layers](#two-testing-layers). |
| `conftest.py` | Test parametrization (`pytest_generate_tests`), the `--write_api`/`--overwrite` options and the interactive write confirmation prompt. |
| `defaults.py` | `TestDefaults` (tokens, IDs, name/cid/uuid/macid generators), `API_DEFAULTS` scrubbing map, and the `FunctionResponses*` factories / `build_bypass_v*_response()` helpers. |
| `utils.py` | `YAMLWriter`, `parse_args()`, `assert_test()`, `api_scrub()` and the readable-diff helpers used to compare or write fixtures. |
| `aiohttp_mocker.py` | `AiohttpMockSession` / `AiohttpClientMockResponse` - simulate `aiohttp` responses for `TestApiFunc`. |
| `call_json.py` | Device-list builder (`DeviceList`), login/`get_devices()` responses and `ALL_DEVICE_MAP_DICT`. |
| `call_json_<type>.py` | Per-device-type `get_details()` and method responses (`outlets`, `switches`, `fans`, `bulbs`, `purifiers`, `humidifiers`, `thermostat`). |
| `test_<type>.py` | Parametrized device tests (`test_outlets`, `test_bulbs`, `test_fans`, `test_switches`, `test_purifiers`, `test_humidifiers`). |
| `test_all_devices.py` | Asserts every device in each module has a `DETAILS_RESPONSES` entry, and tests `get_devices()` instantiates the expected device counts. |
| `test_auth.py` | `VeSyncAuth` tests - credentials, token-file persistence, login flow, re-auth and error handling. |
| `test_colors.py` | Plain unit tests for `utils/colors.py` (`RGBNightlightColor`); no API fixtures. |
| `test_x_vesync_login.py` | Current login-flow tests using `TestBase` and `TestApiFunc`. |
| `test_x_vesync_api_responses.py` | Current `async_call_api()` error-handling tests via `TestApiFunc`. |
| `xtest_x_*.py` | Legacy tests, not collected by pytest. Kept for reference only. |

## Running the tests

There are two pytest command line arguments built into the tests to specify when to write the api data to YAML files or when to overwrite the existing API calls in the YAML files.

To run a tests for development on existing devices or if you are not ready to write the api calls yet:

```bash
# Through pytest
pytest

# or through tox
tox -e testenv # you can also use the environments lint (pylint), flake8, mypy, ruff
```

If developing a new device and it is completed and thoroughly tested, pass the `--write_api` to pytest. Be sure to include the `--` before the argument in the tox command.

```bash
pytest --write_api

tox -e testenv -- --write_api
```

If fixing an existing device where the API call was incorrect or the api has changed, pass `--write_api` and `--overwrite` to pytest. Both arguments need to be provided to overwrite existing API data already in the YAML files.

```bash
pytest --write_api --overwrite

tox -e testenv -- --write_api --overwrite
```

### Write confirmation prompt

Because `--write_api` and `--overwrite` change the recorded fixtures, they trigger a one-time confirmation prompt at the start of the session:

- In an **interactive terminal** you will be asked to confirm before any files are written. Answer `y` to continue.
- In a **non-interactive/CI session** the run aborts with an error unless you explicitly opt in by setting `PYTEST_CONFIRM=1` in the environment.
- Passing `--overwrite` without `--write_api` is an error - both are required to overwrite.

A plain `pytest` run (no write flags) never prompts and never modifies fixtures.

## Testing Process

The first test run verifies that all of the devices defined in each pyvesync module have a corresponding response in each `call_json_DEVICE` module. This verifies that when a new device is added, a corresponding response is added to be tested.

The testing framework takes the approach of verifying the response and request of each API call separately. The request side of the call is verified by recording the request for a mocked call. The requests are recorded into YAML files in the `api` folder of the tests directory, grouped in folders by module and file by device type.

The response side of the API is tested through the use of responses that have been documented in the `call_json` files and the values specified in the `TestDefaults` class (`defaults.py`) and the per-device-type `*Defaults` classes (e.g. `OutletDefaults` in `call_json_outlets.py`).

### Test IDs

Every generated test is given a readable ID of the form `{device}.{setup_entry}.{method}`, for example `outlets.ESW15-USA.turn_on` or `bulbs.ESL100CW.update`. This makes it easy to run a single case:

```bash
pytest -k "outlets.ESW15-USA.turn_on"
```

## File Structure

### Device Responses and Details

The call_json files contain all of the response data for each device type. The following call_json files are included in the test directory:

- `call_json.py` - general API responses, including `login()` and `get_devices()`. The device list from the `get_devices()` can be used to create the device list response for all devices.
- `call_json_outlets.py` - API responses for the outlets
- `call_json_switches.py` - API responses for the switches
- `call_json_fans.py` - API responses for the fans
- `call_json_bulbs.py` - API responses for the bulbs
- `call_json_purifiers.py` - API responses for the air purifiers
- `call_json_humidifiers.py` - API responses for the humidifiers
- `call_json_thermostat.py` - API responses for the thermostats

#### call_json.py

The `call_json.py` file contains the functions to build the `get_devices()` response containing the device list and each item on the device list. The `DeviceList` class contains the `device_list_response()` method which returns the full device list response based on the defined device types (model number(s)) or types (outlets, fans, etc.). The `device_list_item()` classmethod builds the individual device list item that is used to instantiate the device object. The default values for device configuration values are pulled from the `TestDefaults` class in the `defaults.py` module for consistency.

#### call_json_DEVICE.py

Each device module has its own `call_json` file that follows a consistent structure:

- **`<TYPE>` list** (e.g. `OUTLETS`, `BULBS`) - the list of setup entries, derived from `device_map.<type>_modules`. `test_all_devices.py` asserts this length matches `DETAILS_RESPONSES`.
- **`<Type>Defaults` class** (e.g. `OutletDefaults`) - default state values (statuses, voltage, brightness, etc.) shared across that device type's responses.
- **`DETAILS_RESPONSES` dict** - maps each setup entry to its `get_details()` response as a `(response, status)` tuple. By convention the response bodies are held on a `{DeviceType}Details` class, but the class name and attribute names do not matter - `DETAILS_RESPONSES` is the lookup that the tests actually use.
- **`METHOD_RESPONSES` dict** - maps each setup entry to a `defaultdict` of per-method responses (see below).

Adding a new device usually only requires adding its setup entry's `get_details()` response to `DETAILS_RESPONSES`, since the setup-entry list is derived automatically from the device map.

The responses for device methods are also defined in the `call_json_DEVICE` module. The `METHOD_RESPONSES` dictionary uses a defaultdict imported from `defaults.py` with a simple `{"code": 0, "msg": None}` as the default value (`FunctionResponsesV1` and `FunctionResponsesV2` wrap that in the Bypass V1/V2 response envelopes). The `METHOD_RESPONSES` dictionary is created with keys of device setup entry and values as the defaultdict object. From here the method responses can be added to the defaultdict object for specific scenarios.

```python
from defaults import FunctionResponses
from copy import deepcopy

device_types = ['dev1', 'dev2']

# defaultdict with default value - {"code": 0, "msg": None}
method_response = FunctionResponses

# Use deepcopy so each device gets an independent defaultdict
device_responses = {dev_type: deepcopy(method_response) for dev_type in device_types}

# Define response for specific device & method
device_responses['dev1']['special_method'] = {'response': 'special response', 'msg': 'special method'}

# The default factory can be changed for a single device type since deepcopy is used.
device_responses['dev2'].default_factory = lambda: {'new_code': 0, 'msg': 'success', 'payload': {}}
```

The test sets the mocked `async_call_api()` return value as a tuple of the response and status code, e.g. `mock_api.return_value = (response_dict, 200)`.

The method responses can also be a function that accept one argument that contains the kwargs used in the method call. This allows for more complex responses based on the method call.

The test will know whether it is a straight value or function and call it accordingly.

For example, this is the set status response of the valceno bulb:

```python
def valceno_set_status_response(kwargs=None):
    default_resp = {
        "traceId": TestDefaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": TestDefaults.trace_id,
            "code": 0,
            "result": {
                "enabled": "on",
                "colorMode": "hsv",
                "brightness": TestDefaults.brightness,
                "colorTemp": TestDefaults.color_temp,
                "hue": TestDefaults.color.hsv.hue*27.7778,
                "saturation": TestDefaults.color.hsv.saturation*100,
                "value": TestDefaults.color.hsv.value
            }
        }
    }
    if isinstance(kwargs, dict):
        if kwargs.get('hue') is not None:
            default_resp['result']['result']['hue'] = kwargs['hue'] * 27.7778
        if kwargs.get('saturation') is not None:
            default_resp['result']['result']['saturation'] = kwargs['saturation'] * 100
        if kwargs.get('value') is not None:
            default_resp['result']['result']['value'] = kwargs['value']
    return default_resp


XYD0001_RESP = {
    'set_brightness': valceno_set_status_response,
    'set_color_temp': valceno_set_status_response,
    'set_hsv': valceno_set_status_response,
    'set_rgb': valceno_set_status_response,
}

METHOD_RESPONSES['XYD0001'].update(XYD0001_RESP)
```

### **`api`** directory with `YAML` files

API requests recorded from the mocked `async_call_api()` method. The `api` directory contains folders for each module and files for each device type (setup entry). The structure of the YAML files is:

**File** `src/tests/api/vesyncoutlet/ESO15-TB.yaml`

```yaml
turn_off:
  headers:
    accept-language: en
    accountId: sample_id
    appVersion: 2.8.6
    content-type: application/json
    tk: sample_tk
    tz: America/New_York
  json_object:
    acceptLanguage: en
    accountID: sample_id
    status: 'off'
    switchNo: 3
    timeZone: America/New_York
    token: sample_tk
    uuid: ESO15-TB-UUID
  method: put
  url: /outdoorsocket15a/v1/device/devicestatus
```

### **`defaults.py`** - default value factory for tests

The recorded requests are automatically scrubbed with these default values to remove sensitive information and normalize the data. Any new API calls added to `call_json_` files should use the default values wherever possible.

```python
from defaults import TestDefaults

# Default Class variables
token = TestDefaults.token
account_id = TestDefaults.account_id
trace_id = TestDefaults.trace_id
active_time = TestDefaults.active_time
# The default Color dataclass exposes rgb and hsv models. Conversion is
# automatically done regardless of the input color model. This is to normalize
# any API calls that involve changing color
color = TestDefaults.color  # Color(RGB(50, 100, 225))
brightness = TestDefaults.brightness
color_temp = TestDefaults.color_temp

# Default values that use methods
device_name = TestDefaults.name(setup_entry="ESL100") # returns 'ESL100-NAME'
device_cid = TestDefaults.cid(setup_entry="ESL100") # returns 'ESL100-CID'
device_uuid = TestDefaults.uuid(setup_entry="ESL100") # returns 'ESL100-UUID'
device_mac = TestDefaults.macid(setup_entry="ESL100") # returns 'ESL100-MACID'
```

### **`base_test_cases.py`** - base test classes

The `base_test_cases` module contains the base class with a fixture that instantiates the VeSync object and patches `async_call_api()` automatically, allowing a return value to be set:

```python
from base_test_cases import TestBase
from defaults import FunctionResponses


class TestDevice(TestBase):

    def test_details(self):
        vesync_instance = self.manager
        mock_api_object = self.mock_api  # patches VeSync.async_call_api
        mock_api_object.return_value = (FunctionResponses['default'], 200)
        caplog = self.caplog
        assert vesync_instance.enabled is True
```

## Test Structure

Each device module in the pyvesync library has an associated testing module, for example, `vesyncswitch` and `test_switches`. Humidifiers, air purifiers and fans each have their own test modules (`test_humidifiers.py`, `test_purifiers.py`, `test_fans.py`).

The class inherits from the `TestBase` class in `base_test_cases.py` and is parametrized by `pytest_generate_tests` based on the method. The parameters are defined by the class attributes. The `base_methods` and `device_methods` class attributes define the method and arguments in a list of lists with the first item, the method name and the second optional item, the method kwargs. The `base_methods` class attribute defines methods that are common to all devices. The `device_methods` class attribute defines methods that are specific to the device type.

This is an examples of the class definition:

```python
from base_test_cases import TestBase

class TestBulbs(TestBase):
    device = 'bulbs'
    bulbs = call_json_bulbs.BULBS
    base_methods = [['turn_on'], ['turn_off'],
                    ['set_brightness', {'brightness': 50}]]
    device_methods = {
        'ESL100CW': [['set_color_temp', {'color_temp': 50}]]
    }
```

The methods are then parametrized based on those values. For most device additions, the only thing that needs to be added is the device type in the `DETAILS_RESPONSES` and possibly a response in the `METHOD_RESPONSES` dictionary.

## Adding a new device to the test suite

1. **Add the device to `pyvesync`** first - once its map entry is in `device_map.<type>_modules`, its setup entry is automatically included in the test module's `<TYPE>` list.
2. **Add a `get_details()` response** for the setup entry to `DETAILS_RESPONSES` in the matching `call_json_<type>.py`. `test_all_devices.py` fails until every device has one.
3. **Add non-default method responses** to `METHOD_RESPONSES[setup_entry]` only if the device needs something other than the default `{"code": 0, "msg": None}` envelope.
4. **Add device-specific methods** to the test class's `device_methods` dict if the device supports methods beyond the shared `base_methods`. Devices that only use existing base/device methods are covered automatically by parametrization.
5. **Record the fixtures** with `pytest --write_api` (or `--write_api --overwrite` when an existing device's API changed), then commit the new/updated YAML files under `src/tests/api/`.
6. **Run `pytest`** with no flags to confirm the recorded requests match.

See the docstrings in the modules for more information.
