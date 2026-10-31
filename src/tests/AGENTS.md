# AGENTS.md (src/tests)

Guidance for AI coding agents working in the pyvesync test suite. This file
adds to the repository-root [AGENTS.md](../../AGENTS.md); the contribution rules
there (packet captures only, real-hardware verification, one change per PR)
apply here too. Human-oriented background: [README.md](README.md) and
[docs/development/testing.md](../../docs/development/testing.md).

## What the suite tests

Device tests check the **exact API request** each device method sends: URL,
HTTP method, headers and JSON body. A mocked response is fed back to the
method. Requests are recorded once into YAML fixtures and compared on every
later run. The point is to catch unintended changes to what the library sends
to VeSync. The fixtures are not a model of how VeSync responds.

## Running

```bash
pytest                                   # from repo root; testpaths = src/tests
pytest src/tests/test_outlets.py         # one module
pytest src/tests/test_outlets.py -k "ESW15-USA"   # filter by test ID
pytest --write_api                       # record fixtures that don't exist yet
pytest --write_api --overwrite           # re-record ALL fixtures (API changed)
```

- `--write_api` and `--overwrite` ask for an interactive `y/N` confirmation at
  session start. In a non-interactive shell (agents, CI) the run aborts with a
  `UsageError` unless you set `PYTEST_CONFIRM=1`, e.g.
  `PYTEST_CONFIRM=1 pytest src/tests/test_outlets.py --write_api`.
- `--overwrite` without `--write_api` exits with an error.
- `pyproject.toml` sets `log_cli = true`, so output is verbose. Add
  `-o log_cli=false` for quieter runs. Don't pass `-p no:logging`: the tests
  depend on the `caplog` fixture.
- Narrow any fixture-writing run to the module or test you changed. Never run
  `--write_api --overwrite` across the whole suite to make failures go away.

## Layout

There is no `__init__.py`. Modules import each other by bare name
(`from base_test_cases import TestBase`, `import call_json_outlets`).

### Infrastructure

| File | Purpose |
| ---- | ------- |
| `conftest.py` | `--write_api` / `--overwrite` options, the confirmation prompt, and `pytest_generate_tests()`, which parametrizes `test_details` / `test_methods` from class attributes |
| `base_test_cases.py` | `TestBase` (patches `VeSync.async_call_api`) and `TestApiFunc` (patches `aiohttp.ClientSession`) |
| `utils.py` | `parse_args()` (mock call args to dict), `assert_test()` (compare or write YAML), `api_scrub()`, `YAMLWriter`, `deep_diff()` / `dicts_equal()` for readable assertion diffs |
| `defaults.py` | `TestDefaults` (token, account ID, email, deterministic `name()` / `cid()` / `uuid()` / `macid()` per setup entry), `API_DEFAULTS` scrub map, `FunctionResponses` / `FunctionResponsesV1` / `FunctionResponsesV2`, `build_bypass_v1_response()` / `build_bypass_v2_response()` |
| `aiohttp_mocker.py` | `AiohttpMockSession` / `AiohttpClientMockResponse` used by `TestApiFunc` |
| `call_json.py` | `ALL_DEVICE_MAP_DICT` (setup_entry to device map), `DeviceList` (builds device-list entries and `get_devices()` responses), `LoginRequests` / `LoginResponses`, `DETAILS_BADCODE`, default headers |

### Response data: `call_json_<type>.py`

One per device type: `outlets`, `switches`, `bulbs`, `fans`, `purifiers`,
`humidifiers`, `thermostat`. Each module has:

- A setup-entry list taken from `device_map.<type>_modules` (e.g.
  `OUTLETS = [m.setup_entry for m in outlet_modules]`; purifiers use
  `PURIFIER_MODELS`) and a matching `<TYPE>S_NUM` count.
- `DETAILS_RESPONSES`: `setup_entry` to the `get_details()` response dict (or a
  callable returning it). Every setup entry must have one.
- `METHOD_RESPONSES`: `setup_entry` to a `defaultdict` of method responses.
  The default factory returns a generic success body. Override only the methods
  whose response the device actually parses. Values may be callables that take
  the method kwargs.

Response values are plain dicts; the test supplies the status code
(`mock_api.return_value = resp_dict, 200`). The module docstrings in
`call_json_*.py` that describe `(response, status)` tuples are out of date, so
don't store tuples.

Response bodies must reflect real captured responses (scrubbed). Do not invent
fields to make a code path run.

### Test modules

| File | Covers |
| ---- | ------ |
| `test_outlets.py`, `test_switches.py`, `test_bulbs.py`, `test_fans.py`, `test_purifiers.py`, `test_humidifiers.py` | Device requests via `TestBase`, parametrized per setup entry |
| `test_all_devices.py` | Every device has a `DETAILS_RESPONSES` entry (`test_device_tests`); `get_devices()` request |
| `test_auth.py` | `VeSyncAuth`: init/region, credentials, token-file persistence, login and re-auth flows |
| `test_colors.py` | Plain unit tests for `utils/colors.py`, no fixtures |
| `test_x_vesync_login.py` | Login flow (`TestBase` and `TestApiFunc`). Current, not legacy |
| `test_x_vesync_api_responses.py` | `async_call_api()` error handling: rate limits, server errors, status codes (`TestApiFunc`). Current, not legacy |
| `xtest_x_*.py` | Legacy, not collected (filename doesn't start with `test_`). Don't extend them |

`conftest.py` skips auto-parametrization for any module whose name contains
`test_x`, so those modules define their own tests normally.

### Fixtures: `api/`

`api/<device module>/<setup_entry>.yaml`. The folder is the module of the
**device class** under test (`vesyncoutlet`, `vesyncpurifier`, ...), not the
test file. `api/vesync/VeSync.yaml` holds manager-level calls. Each file maps
method name to the recorded request:

```yaml
turn_off:
  headers: { ... }
  json_object: { ... }
  method: put
  url: /outdoorsocket15a/v1/device/devicestatus
```

## How a device test works

`TestBase` provides `self.manager` (a `VeSync` with fake token/account and
`redact = False`), `self.mock_api`, `self.caplog`, `run_in_loop()` and
`get_device(product_type, setup_entry)`. Tests are synchronous; coroutines run
through `run_in_loop()` on a per-test event loop (no pytest-asyncio).

```text
mock_api.return_value = (response_dict, 200)    # from DETAILS/METHOD_RESPONSES
obj = self.get_device('outlets', setup_entry)   # built from ALL_DEVICE_MAP_DICT
self.run_in_loop(getattr(obj, method), **kwargs)
all_kwargs = parse_args(self.mock_api)          # url, method, json_object, headers
assert assert_test(method_call, all_kwargs, setup_entry,
                   self.write_api, self.overwrite)
```

The outlet and switch tests then feed a bad response (`DETAILS_BADCODE`, or
`(None, 400)` for the legacy 7A outlet) and assert the method fails cleanly: it
returns `False` or logs an error.

`assert_test()` scrubs headers and body with `api_scrub()` first: `cid`, `uuid`
and `macid` become `<deviceType>-CID` etc., and keys in `API_DEFAULTS` (token,
accountID, traceId, ...) become fixed defaults. Then:

- fixture exists: request must equal it, or the assertion prints a diff;
- fixture missing, no `--write_api`: returns `False`, so the **test fails**;
- fixture missing, `--write_api`: writes it and passes;
- `--write_api --overwrite`: rewrites it unconditionally and passes.

### Parametrization

```python
class TestOutlets(TestBase):
    device = 'outlets'                       # names the attribute holding the device list
    outlets = call_json_outlets.OUTLETS      # must match the value of `device`
    base_methods = [['turn_on'], ['turn_off']]          # run on every device
    device_methods = {                                  # extra, per setup entry
        'ESW15-USA': [['turn_on_nightlight'], ['get_weekly_energy']],
    }
```

- Method entries are `[name]` or `[name, {kwargs}]`, e.g.
  `['set_brightness', {'brightness': 50}]`.
- `test_details` runs `update` for every device; `test_methods` runs every
  device x (`base_methods` + its `device_methods`).
- Test IDs embed the method entry as a list: `outlets.ESW15-USA.['turn_on']`
  (details tests end in `.update`). Filter with `-k "ESW15-USA"` rather than
  typing a full ID.
- The `device_methods` key is the device map's `setup_entry`, not a `dev_types`
  string.

## Common tasks

### New model of an existing device type

1. Add the `device_map.py` entry. The setup entry is picked up automatically.
2. Add `DETAILS_RESPONSES[setup_entry]` in `call_json_<type>.py`, and
   `METHOD_RESPONSES[setup_entry][...]` for methods that parse a response.
   `test_all_devices.py::test_device_tests` fails until the details response exists.
3. Add device-specific methods to `device_methods` in `test_<type>.py`.
4. `PYTEST_CONFIRM=1 pytest src/tests/test_<type>.py --write_api`, then rerun
   without flags. Review the generated YAML against the packet capture before
   committing.

### New method on existing devices

Add it to `base_methods` (if every device
of the type supports it) or `device_methods`, add responses if needed, and
write fixtures as above. Existing fixtures are untouched because only missing
methods are written.

### Intentional request change

When fixing a wrong payload, rerun the affected
module with `--write_api --overwrite`. Confirm that only the intended YAML
entries changed (`git diff src/tests/api`), and explain the change in the PR.

### Unexpected fixture mismatch

The request changed. Treat it as a regression
until proven otherwise; don't overwrite the fixture to make it pass.

### New device type, thermostats, air fryers

`call_json_thermostat.py`
exists, but there is no `test_thermostat.py`, and neither thermostats nor air
fryers are in `call_json.ALL_DEVICE_MAP_MODULES`, so `get_device()` cannot
build them yet. Adding coverage means registering the type's `*_modules` in
`call_json.py`, adding a `call_json_<type>.py`, a `test_<type>.py` following
`test_outlets.py`, and a count assertion in `test_device_tests`. That is its
own PR.

## Conventions

- `src/tests` is excluded from ruff and pre-commit. Keep the existing style of
  neighbouring tests and don't reformat files you aren't changing.
- Use `TestDefaults` and the response builders. Never put real tokens, account
  IDs, emails, CIDs or MACs in tests or fixtures.
- Don't hand-edit YAML fixtures. Change the code or the response data and
  regenerate.
- Commit regenerated fixtures in the same PR as the code change that produced them.
