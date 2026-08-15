# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository's test suite.

## Test Architecture Overview

Tests verify API requests made by pyvesync devices at two levels:

1. **`TestBase` (call_api level)** - Patches `VeSync.async_call_api()` to mock all device method calls. This is the primary testing approach for device tests. The mock intercepts the call before any HTTP request is made, capturing the url, method, json_object, and headers arguments.

2. **`TestApiFunc` (aiohttp level)** - Patches `aiohttp.ClientSession` directly, testing the full HTTP request/response cycle. Uses `AiohttpMockSession` from `aiohttp_mocker.py` to simulate aiohttp responses with proper status codes, bytes content, and async context managers. Used for login tests and API error handling (rate limits, server errors, status codes).

## Parametrized Test Generation

Tests are auto-parametrized by `conftest.py:pytest_generate_tests()` based on class attributes:

```python
class TestOutlets(TestBase):
    device = 'outlets'                    # Device category name
    outlets = call_json_outlets.OUTLETS   # List of setup_entry strings (must match `device` name)
    base_methods = [['turn_on'], ['turn_off']]  # Methods tested on ALL devices
    device_methods = {                    # Methods tested on SPECIFIC devices
        'ESW15-USA': [['turn_on_nightlight'], ['get_weekly_energy']],
    }
```

The `device` attribute names the list attribute to look up. So `device = 'outlets'` means conftest reads `cls.outlets` for the device list. This generates two test functions:

- **`test_details(setup_entry, method)`** - Parametrized with each setup_entry + `'update'`. Tests `get_details()` request against YAML fixtures.
- **`test_methods(setup_entry, method)`** - Parametrized as cartesian product of devices x (base_methods + device-specific methods). Tests each method's request against YAML fixtures.

Test IDs follow the pattern: `{device}.{setup_entry}.{method}` (e.g., `outlets.ESW15-USA.turn_on`).

## YAML API Fixture System

API requests are recorded and verified via YAML files in `src/tests/api/{module}/{setup_entry}.yaml`. Each YAML file maps method names to the full request captured from the mocked `call_api()`:

```yaml
turn_off:
  headers: { ... }
  json_object: { ... }
  method: put
  url: /outdoorsocket15a/v1/device/devicestatus
```

The flow in each test method:

1. Set `mock_api.return_value` to the response from `call_json_*` module
2. Instantiate device via `self.get_device(product_type, setup_entry)`
3. Call the device method (e.g., `outlet_obj.turn_on()`)
4. `parse_args(self.mock_api)` extracts the captured call_api arguments
5. `assert_test()` scrubs sensitive data via `api_scrub()`, then either:
   - **Normal run**: Compares against existing YAML fixture (assert equal)
   - **`--write_api`**: Writes new fixtures for methods without existing YAML
   - **`--write_api --overwrite`**: Overwrites all existing YAML fixtures

Sensitive values (tokens, account IDs, UUIDs) are normalized to defaults by `api_scrub()` before comparison/writing.

## File Responsibilities

### Test infrastructure

| File | Purpose |
| ---- | ------- |
| `conftest.py` | `pytest_generate_tests()` for parametrization, `--write_api`/`--overwrite` CLI options, interactive confirmation prompt |
| `base_test_cases.py` | `TestBase` (patches `async_call_api`) and `TestApiFunc` (patches `ClientSession`). Both provide `self.manager`, `self.mock_api`, `self.caplog`, `run_in_loop()` |
| `utils.py` | `YAMLWriter` (read/write YAML fixtures), `parse_args()` (extract mock call args), `assert_test()` (compare or write YAML), `api_scrub()` (normalize sensitive data), `deep_diff()`/`dicts_equal()` (readable diff output) |
| `defaults.py` | `TestDefaults` (token, account_id, trace_id, name/cid/uuid/macid generators), `API_DEFAULTS` (scrubbing map), response builder functions (`build_bypass_v1_response`, `build_bypass_v2_response`) |
| `aiohttp_mocker.py` | `AiohttpMockSession` and `AiohttpClientMockResponse` - simulate aiohttp `ClientSession.request()` responses with async context manager support |

### Response data (`call_json_*`)

| File | Purpose |
| ---- | ------- |
| `call_json.py` | Aggregates all device modules into `ALL_DEVICE_MAP_DICT`. Contains `DeviceList` (builds `get_devices()` responses), `LoginRequests`/`LoginResponses`, `DeviceDetails`, default headers |
| `call_json_outlets.py` | `OUTLETS` list (from `device_map.outlet_modules`), `DETAILS_RESPONSES` dict, `METHOD_RESPONSES` defaultdict |
| `call_json_bulbs.py` | Same pattern for bulbs |
| `call_json_fans.py` | Same pattern for fans |
| `call_json_switches.py` | Same pattern for switches |
| `call_json_purifiers.py` | Same pattern for purifiers |
| `call_json_humidifiers.py` | Same pattern for humidifiers |
| `call_json_thermostat.py` | Same pattern for thermostats |

Each `call_json_*` module follows the same structure:

- `DEVICE_TYPE_LIST` - pulled from `device_map.*_modules` setup entries
- `DETAILS_RESPONSES` - dict mapping setup_entry to get_details() API response
- `METHOD_RESPONSES` - dict of setup_entry to `defaultdict` of method responses. Default factory returns `{"code": 0, "msg": None}`. Device-specific responses override specific keys. Values can be callables accepting kwargs.

### Test files

| File | Tests |
| ---- | ----- |
| `test_outlets.py` | Outlet device methods via `TestBase` |
| `test_bulbs.py` | Bulb device methods via `TestBase` |
| `test_fans.py` | Fan device methods via `TestBase` |
| `test_switches.py` | Switch device methods via `TestBase` |
| `test_purifiers.py` | Purifier device methods via `TestBase` |
| `test_humidifiers.py` | Humidifier device methods via `TestBase` |
| `test_all_devices.py` | Verifies all devices have DETAILS_RESPONSES entries; tests `get_devices()` |
| `test_auth.py` | `VeSyncAuth` tests (credentials, token-file persistence, login flow, re-auth, error handling) via `TestBase` |
| `test_colors.py` | Plain unit tests for `utils/colors.py` (`RGBNightlightColor`), no API fixtures |
| `test_x_vesync_login.py` | Login flow tests using both `TestBase` and `TestApiFunc` |
| `test_x_vesync_api_responses.py` | Tests `async_call_api` error handling (rate limits, server errors, status codes) via `TestApiFunc` with `AiohttpMockSession` |
| `xtest_x_*.py` | Legacy tests (prefixed with `x` to skip collection), kept for reference |

## Adding Tests for a New Device

1. **`call_json_{device_type}.py`**: Add setup_entry to the module's list (auto-derived from `device_map.*_modules`). Add response to `DETAILS_RESPONSES[setup_entry]`. Add any non-default method responses to `METHOD_RESPONSES[setup_entry]`.

2. **`test_{device_type}.py`**: If the device uses existing base/device methods, it's automatically included through the parametrization. Add device-specific methods to `device_methods` dict if needed.

3. **Run `pytest --write_api`** to generate YAML fixtures for new devices. Use `--write_api --overwrite` only when an existing API has changed.

## Key Testing Patterns

### TestBase flow (device tests)

```text
mock_api patches VeSync.async_call_api
    -> set mock_api.return_value = (response_dict, 200)
    -> get_device() instantiates device from DeviceList.device_list_item()
    -> call device method (runs against mock)
    -> parse_args() extracts url, method, json_object, headers from mock
    -> assert_test() compares scrubbed request against YAML fixture
```

### TestApiFunc flow (login/error tests)

```text
mock patches aiohttp.ClientSession
    -> mock.return_value.request.return_value = AiohttpMockSession(...)
    -> call manager method (makes real async_call_api call)
    -> AiohttpMockSession returns mock response with status/bytes
    -> assert response handling (exceptions raised, state changes, etc.)
```

### Response builder helpers

- `build_bypass_v1_response()` - Wraps result in standard V1 envelope with traceId, code, msg
- `build_bypass_v2_response()` - Wraps result in nested V2 envelope (outer result containing inner result with its own code/traceId)
- `FunctionResponses` / `FunctionResponsesV1` / `FunctionResponsesV2` - Default response factories for each API version
