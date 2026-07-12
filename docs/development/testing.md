# Testing

Tests use pytest with parametrized fixtures. The test suite verifies API requests made by pyvesync devices at two levels.

## Running Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest src/tests/test_outlets.py

# Run with tox (all environments)
tox

# Individual tox environments
tox -e 3.11     # pytest with Python 3.11
tox -e 3.12     # pytest with Python 3.12
tox -e 3.13     # pytest with Python 3.13
tox -e lint     # pylint
tox -e flake8   # flake8 + pydocstrings
tox -e mypy     # type checking
tox -e ruff     # ruff linting
```

## Test Architecture

### TestBase - Device Method Tests

`TestBase` in `src/tests/base_test_cases.py` patches `VeSync.async_call_api()` to mock all device method calls. This is the primary testing approach for device tests. The mock intercepts the call before any HTTP request is made, capturing the `url`, `method`, `json_object`, and `headers` arguments.

The test flow:

1. Set `mock_api.return_value` to the response from the `call_json_*` module
2. Instantiate device via `self.get_device(product_type, setup_entry)`
3. Call the device method (e.g., `outlet_obj.turn_on()`)
4. `parse_args(self.mock_api)` extracts the captured `call_api` arguments
5. `assert_test()` scrubs sensitive data via `api_scrub()`, then compares against the existing YAML fixture

### TestApiFunc - HTTP-level Tests

`TestApiFunc` patches `aiohttp.ClientSession` directly, testing the full HTTP request/response cycle. Uses `AiohttpMockSession` from `aiohttp_mocker.py` to simulate aiohttp responses. Used for login tests and API error handling (rate limits, server errors, status codes).

## Parametrized Test Generation

Tests are auto-parametrized by `conftest.py:pytest_generate_tests()` based on class attributes:

```python
class TestOutlets(TestBase):
    device = 'outlets'                    # Device category name
    outlets = call_json_outlets.OUTLETS   # List of setup_entry strings
    base_methods = [['turn_on'], ['turn_off']]  # Methods tested on ALL devices
    device_methods = {                    # Methods tested on SPECIFIC devices
        'ESW15-USA': [['turn_on_nightlight'], ['get_weekly_energy']],
    }
```

This generates two test functions:

- **`test_details(setup_entry, method)`** - Tests `get_details()` request against YAML fixtures.
- **`test_methods(setup_entry, method)`** - Tests each method's request against YAML fixtures.

Test IDs follow the pattern: `{device}.{setup_entry}.{method}` (e.g., `outlets.ESW15-USA.turn_on`).

## YAML API Fixtures

API requests are recorded and verified via YAML files in `src/tests/api/{module}/{setup_entry}.yaml`. Each YAML file maps method names to the full request captured from the mocked `call_api()`:

```yaml
turn_off:
  headers: { ... }
  json_object: { ... }
  method: put
  url: /outdoorsocket15a/v1/device/devicestatus
```

Sensitive values (tokens, account IDs, UUIDs) are normalized to defaults by `api_scrub()` before comparison or writing.

### Writing API Fixtures

To generate or update YAML fixtures for new devices:

```bash
# Write fixtures for new devices (does not overwrite existing)
pytest --write_api

# Overwrite all existing fixtures (use with caution)
pytest --write_api --overwrite
```

## Adding Tests for a New Device

1. **`call_json_{device_type}.py`**: Add setup_entry to the module's device list. Add response to `DETAILS_RESPONSES[setup_entry]`. Add any non-default method responses to `METHOD_RESPONSES[setup_entry]`.

2. **`test_{device_type}.py`**: If the device uses existing base/device methods, it is automatically included through parametrization. Add device-specific methods to `device_methods` dict if needed.

3. **Run `pytest --write_api`** to generate YAML fixtures for new devices.
