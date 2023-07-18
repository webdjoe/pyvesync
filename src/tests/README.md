# The pyvesync testing library

This is the testing suite for the pyvesync library. Each device that is added must include tests. This helps to maintain the consistency of the API as new devices are added and the backend is refactored.

I've built a relatively simple framework to ease the burden of writing tests. There are some old tests that I had previously written that I've kept as I build the new framework but these tests were not comprehensive or portable. The files that begin with `test_x_` are these previous tests and can safely be ignored.

The tests primarily run each API call for each device and record the request details in YAML files in the `tests\API` directory. These files are then used to verify the request when the test is run again.

The structure of the framework is as follows:

1. `call_json.py` - This file contains general functions and the device list builder. This file does not need to be edited when adding a device.
2. `call_json_DEVICE.py` - This file contains device specific responses such as the `get_details()` response and specific method responses. This file pulls in the device type list from each module. The minimum addition is to add the appropriate response to the `DeviceDetails` class and the device type associated with that response in the `DETAILS_RESPONSES` dictionary. This file also contains the `DeviceDefaults` class which are specific to the device.
3. `test_DEVICE.py`  - Each module in pyvesync has it's own test module, typically with one class that inherits the `utils.BaseTest` class. The class has two methods - `test_details()` and `test_methods()` that are parametrized by `utils.pytest_generate_tests`
4. `utils.py` - Contains the general default values for all devices in the `Defaults` class and the `TestBase` class that contains the fixture that instantiates the VS object and patches the `call_api()` method.
5. `conftest.py` - Contains the `pytest_generate_tests` function that is used to parametrize the tests based on all device types listed in the respective modules.


## Running the tests

There are two pytest command line arguments built into the tests to specify when to write the api data to YAML files or when to overwrite the existing API calls in the YAML files.

To run a tests for development on existing devices or if you are not ready to write the api calls yet:

```bash
# Through pytest
pytest

# or through tox
tox -e testenv # you can also use the environments lint, pylint, mypy
```

If developing a new device and it is completed and thoroughly tested, pass the `--write_api` to pytest. Be sure to include the `--` before the argument in the tox command.

```bash
pytest --write_api

tox -e testenv -- --write_api
```

If fixing an existing device where the API call was incorrect or the api has changed, pass `--write_api` and `overwrite` to pytest. Both arguments need to be provided to overwrite existing API data already in the YAML files.

```bash
pytest --write_api --overwrite

tox -e testenv -- --write_api --overwrite
```

## Testing Process

The first test run verifies that all of the devices defined in each pyvesync module have a corresponding response in each `call_json_DEVICE` module. This verifies that when a new device is added, a corresponding response is added to be tested.

The testing framework takes the approach of verifying the response and request of each API call separately. The request side of the call is verified by recording the request for a mocked call. The requests are recorded into YAML files in the `api` folder of the tests directory, grouped in folders by module and file by device type.

The response side of the API is tested through the use of responses that have been documented in the `call_json` files and the values specified in the `Defaults` and `DeviceDefaults` classes.

## File Structure

### Device Responses and Details

The call_json files contain all of the response data for each device type. The following call_json files are included in the test directory:

   - `call_json.py` - general API responses, including `login()` and `get_devices()`. The device list from the `get_devices()` can be used to create the device list response for all devices.
   - `call_json_outlets.py` - API responses for the outlets
   - `call_json_switches.py` - API responses for the switches
   - `call_json_fans.py` - API responses for the fans
   - `call_json_bulbs.py` - API responses for the bulbs

#### call_json.py

The `call_json.py` file contains the functions to build the `get_devices()` response containing the device list and each item on the device list. The `DeviceList` class contains the `device_list_response(devices_types=None, _types=None)` method which returns the full device list response based on the defined device types (model number(s)) or types (outlets, fans, etc.). The `device_list_item(model)` builds the individual device list item that is used to instantiate the device object. The default values for device configuration values are pulled from the `Defaults` class in the `utils.py` module for consistency.

#### call_json_DEVICE.py

Each device module has it's own `call_json` file. The structure of the files maintains a consistency for easy test definition. The `DeviceDetails` (SwitchDetails, OutletDetails) class contains the `get_details()` responses for each device as a class attribute. The name of the class attribute does not matter.

The `DETAILS_RESPONSES` dictionary contains the device type as the key and references the `DeviceDetails` class attribute as the value. The `DETAILS_RESPONSES` dictionary is used to lookup the appropriate response for each device type.

The responses for device methods are also defined in the `call_json_DEVICE` module. The METHOD_RESPONSES dictionary uses a defaultdict imported from `utils.py` with a simple `{"code": 0, "message": ""}` as the default value. The `METHOD_RESPONSES` dictionary is created with keys of device type and values as the defaultdict object. From here the method responses can be added to the defaultdict object for specific scenarios.

```python
from utils import FunctionResponses 
from copy import deepcopy

device_types = ['dev1', 'dev2']

# defaultdict with default value - ({"code": 0, "msg": None}, 200)
method_response = FunctionResponses 

# Use deepcopy to build the device response dictionary used to test the get_details() method
device_responses = {dev_type: deepcopy(method_response) for dev_type in device_types}

# Define response for specific device & method
# All response must be tuples with (json response, 200)
device_responses['dev1']['special_method'] = ({'response': 'special response', 'msg': 'special method'}, 200)

# The default factory can be change for a single device type since deepcopy is used.
device_responses['dev2'].default_factory = lambda: ({'new_code': 0, 'msg': 'success', {'payload': {}}}, 200)

```

The method responses can also be a function that accept one argument that contains the kwargs used in the method call. This allows for more complex responses based on the method call.

The test will know whether it is a straight value or function and call it accordingly.

For example, this is the set status response of the valceno bulb:

```python

METHOD_RESPONSES = {k: deepcopy(FunctionResponses) for k in BULBS}

def valceno_set_status_response(kwargs=None):
    default_resp = {
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "enabled": "on",
                "colorMode": "hsv",
                "brightness": Defaults.brightness,
                "colorTemp": Defaults.color_temp,
                "hue": Defaults.color.hsv.hue*27.7778,
                "saturation": Defaults.color.hsv.saturation*100,
                "value": Defaults.color.hsv.value
            }
        }
    }
    if kwargs is not None and isinstance(kwargs, dict):
        if kwargs.get('hue') is not None:
            default_resp['result']['result']['hue'] = kwargs['hue'] * 27.7778
        if kwargs.get('saturation') is not None:
            default_resp['result']['result']['saturation'] = kwargs['saturation'] * 100
        if kwargs.get('value') is not None:
            default_resp['result']['result']['value'] = kwargs['value']
    return default_resp, 200


XYD0001_RESP = {
    'set_brightness': valceno_set_status_response,
    'set_color_temp': valceno_set_status_response,
    'set_hsv': valceno_set_status_response,
    'set_rgb': valceno_set_status_response,
}

METHOD_RESPONSES['XYD0001'].update(XYD0001_RESP)


```

### **`api`** directory with `YAML` files

API requests recorded from the mocked `call_api()` method. The `api` directory contains folders for each module and files for each device_type. The structure of the YAML files is:

**File** `tests/api/switches/esl100.yaml`
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

### **`utils.py`** - utility functions and default value factory for tests.

The `utils.py`  file contains several helper functions and classes:

### Default values for API responses and requests

The recorded requests are automatically scrubbed with these default values to remove sensitive information and normalize the data. Any new API calls added to `call_json_` files should use the defaults values wherever possible.

```python
from utils import Defaults

# Default Class variables
token = Defaults.token
account_id = Defaults.account_id
trace_id = Defaults.trace_id
active_time = Defaults.active_time
# The default Color dataclass contains the attributes red, green, blue, hue saturation & value. Conversion is automatically done regardless of the input color model. This is to normalize any API calls that involve changing color
color = Color(red=50, green=100, blue=255)
brightness = Defaults.brightness
color_temp = Defaults.color_temp

# Default values that use methods
device_name = Defaults.name(dev_type="ESL100") # returns 'ESL100-NAME'
device_cid = Defaults.cid(dev_type="ESL100") # returns 'ESL100-CID'
device_uuid = Defaults.uuid(dev_type="ESL100") # returns 'ESL100-UUID'
device_mac = Defaults.macid(dev_type="ESL100") # returns 'ESL100-MACID'
```

The `utils` module contains the base class with a fixture that instantiates the VeSync object and patches `call_api()` automatically, allowing a return value to be set..

```python
from utils import TestBase, FunctionResponses


class TestDevice(TestBase):

    def test_details(self):
        vesync_instance = self.manager
        mock_api_object = self.mock_api # patch('pyvesync.helpers.call_api', autopspec=True)
        mock_api_object.return_value = FunctionResponses['default']
        caplog = self.caplog
        assert vesync_instance.enabled is True

```

## Test Structure

Each module in the pyvesync library has an associated testing module, for example, `vesyncswitches` and `test_switches`. Most testing modules have one class, except for the `test_fans` module, which has separate classes for humidifiers and air purifiers.

The class inherits from the `TestBase` class in `utils.py` and is parametrized by `pytest_generate_tests` based on the method. The parameters are defined by the class attributes. The `base_methods` and `device_methods` class attributes define the method and arguments in a list of lists with the first item, the method name and the second optional item, the method kwargs. The `base_methods` class attribute defines methods that are common to all devices. The `device_methods` class attribute defines methods that are specific to the device type.

This is an examples of the class definition:

```python
from utils import TestBase

class TestBulbs(TestBase):
    device = 'bulbs'
    bulbs = call_json_bulbs.BULBS
      base_methods = [['turn_on'], ['turn_off'],
                      ['set_brightness',   {'brightness': 50}]]
    device_methods = {
        'ESL100CW': [['set_color_temp', {'color_temp': 50}]]
    }
```

The methods are then parametrized based on those values. For most device additions, the only thing that needs to be added is the device type in the `DETAILS_RESPONSES` and possibly a response in the `METHOD_RESPONSES` dictionary.

See the docstrings in the modules for more information.
