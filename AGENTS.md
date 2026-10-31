# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Cursor, Copilot, etc.) working
in the pyvesync repository. This file is self-contained. The human opening the
pull request is responsible for the result, so follow these rules.

AGENTS.md is the single source of agent instructions. `CLAUDE.md` and
`src/tests/CLAUDE.md` only import the AGENTS.md beside them (`@AGENTS.md`) for
Claude Code. Edit the AGENTS.md files and keep the CLAUDE.md files as wrappers.

## Project overview

pyvesync is an async Python library (Python 3.11+) for controlling VeSync smart
home devices: outlets, wall switches, bulbs, fans, air purifiers, humidifiers,
air fryers and thermostats. It uses `aiohttp` for HTTP and `mashumaro` + `orjson`
for (de)serialization. The public entry point is the `VeSync` manager
(`pyvesync/__init__.py` exports only `VeSync`), used as an async context manager.

Authoritative references (read when the topic comes up):

- [docs/development/contributing.md](docs/development/contributing.md): the full
  contribution guide (rules, code style, PR process, release process).
- [docs/development/capturing.md](docs/development/capturing.md): how API
  request/response shapes are captured from the VeSync app.
- [src/tests/AGENTS.md](src/tests/AGENTS.md): agent guide to the test suite
  (layout, fixtures, parametrization, common tasks). Read it before touching
  `src/tests/`.
- [docs/development/testing.md](docs/development/testing.md) and
  [src/tests/README.md](src/tests/README.md): human-oriented test docs.

## Contribution rules (mandatory)

1. **Follow the intended architecture.** Use the three-tier hierarchy below.
   Device state goes in the base `DeviceState` subclass, device methods on the
   device-type base class, models in `models/`, constants in `pyvesync.const`.
   No hardcoded strings or magic numbers.
2. **Never invent API request/response fields.** Every request/response shape
   must come from a real packet capture. If no capture exists for a behavior, it
   cannot be implemented. Say so instead of guessing.
3. **Real-hardware verification is required before merge.** New device support
   and any device-behavior change must be tested on the physical device, and the
   PR must state the model and firmware. Testing only through Home Assistant does
   not count. An agent cannot verify hardware: never claim a device works, and
   flag that a human with the device must test it.
4. **One change per PR.** A single feature, fix, or edit per branch/PR. Do not
   batch unrelated or speculative edits into one large PR; split them.
5. **Provide diagnostic info** when adding a device/feature or diagnosing a bug:
   model, `product_type`, firmware, region, pyvesync and Python version, a
   redacted `DEBUG` log, and `device.last_response`. See contributing.md for the
   per-case lists.

If a request would violate these rules (for example "add support for device X"
with no capture and no hardware to test), do not write speculative code. Explain
the blocker and what is needed to proceed.

## Commands

```bash
# Install dev environment (in a venv)
pip install -e .[dev]

# Tests
pytest                                 # all tests (testpaths = src/tests)
pytest src/tests/test_outlets.py       # one file
PYTEST_CONFIRM=1 pytest --write_api              # write missing YAML fixtures
PYTEST_CONFIRM=1 pytest --write_api --overwrite  # overwrite fixtures (API changed)
# PYTEST_CONFIRM=1 skips the interactive y/N prompt (required without a TTY);
# narrow these runs to the test module you changed.

# Lint, format, type check
ruff check src/pyvesync
ruff format src/pyvesync
mypy src/pyvesync
pylint src/pyvesync
pre-commit run --all-files             # stage changes first

# tox environments (see tox.ini)
tox                  # everything
tox -e 3.11          # pytest (also 3.12, 3.13, 3.14)
tox -e lint          # pylint
tox -e flake8        # flake8 + flake8-docstrings
tox -e mypy          # mypy
tox -e ruff          # ruff check
```

Before handing off a change, run at least `ruff check src/pyvesync`,
`mypy src/pyvesync` and `pytest`.

## Repository layout

```text
src/pyvesync/
  vesync.py             VeSync manager: login, device discovery, update, async_call_api()
  auth.py               VeSyncAuth: login flow, token management, optional token file
  const.py              All constants, enums, modes, feature flags, defaults
  device_map.py         *Map dataclasses + *_modules lists mapping API device types to classes
  device_container.py   DeviceContainer (MutableSet) with .outlets, .bulbs, ... accessors
  vesynchome.py         WIP, not implemented: do not build on it (nor models/home_models.py)
  base_devices/         Tier 1: abstract base class + DeviceState subclass per device type
    vesyncbasedevice.py   VeSyncBaseDevice, VeSyncBaseToggleDevice, DeviceState
    outlet_base.py, switch_base.py, bulb_base.py, fan_base.py, purifier_base.py,
    humidifier_base.py, fryer_base.py, thermostat_base.py
  devices/              Tier 2: concrete device classes (vesyncoutlet.py, vesyncpurifier.py, ...)
  models/               mashumaro request/response dataclasses (one module per device type)
  utils/
    device_mixins.py      BypassV1Mixin, BypassV2Mixin, process_bypassv1/v2_result()
    errors.py             VeSyncError hierarchy, ErrorCodes, ResponseInfo
    helpers.py            Shared helpers
    colors.py             Color types and conversions
    logs.py               LibraryLogger with redaction
src/tests/              pytest suite; YAML request fixtures in src/tests/api/
docs/                   MkDocs site (mkdocs.yml); API reference generated by mkdocstrings
```

## Architecture

### Three-tier device hierarchy

1. **Base classes** (`base_devices/`): one abstract base per device type
   (`VeSyncOutlet`, `VeSyncPurifier`, ...), all rooted at `VeSyncBaseDevice`
   (ABC, Generic over its state type). Each module defines a `DeviceState`
   subclass (`OutletState`, `PurifierState`, ...) that holds **all** state for
   that device type. Public properties and methods for a device type are
   declared on the base class, not on the concrete class.
2. **Concrete devices** (`devices/`): a specific model implemented by combining
   an API mixin with the base class. The mixin comes first in the MRO:

   ```python
   class VeSyncOutlet15A(BypassV1Mixin, VeSyncOutlet):      # Bypass V1 API
   class VeSyncOutletWHOGPlug(BypassV2Mixin, VeSyncOutlet): # Bypass V2 API
   ```

   Mixins provide `call_bypassv1_api()` / `call_bypassv2_api()`; parse results
   with `process_bypassv1_result()` / `process_bypassv2_result()` into a model
   from `models/`. A few legacy devices (e.g. `VeSyncOutlet7A`) use their own
   endpoints and no mixin. Follow the pattern of the closest existing device.
3. **Device map** (`device_map.py`): each product type has a `*Map` dataclass
   (`OutletMap`, `PurifierMap`, ...) and a `*_modules` list. An entry maps the
   API `dev_types` strings to `class_name`, `setup_entry`, display names,
   `features` (enums from `const`) and type-specific config such as modes and
   levels. `get_device_config()` and the `get_<type>()` helpers look entries up.

### Models and constants

- Request/response models subclass `RequestBaseModel` / `ResponseBaseModel` from
  `models/base_models.py`. Field names must match the API's JSON keys exactly,
  which is why `models/` relaxes ruff naming rules (N802, N803, N804, N815).
- Every constant, mode, default and feature flag lives in `pyvesync.const`, as a
  `StrEnum` / `IntEnum` where applicable. Use `DeviceStatus.ON`, not `'on'`.

### Method naming

| Pattern                                    | Use                  | Example                                   |
| ------------------------------------------ | -------------------- | ----------------------------------------- |
| `turn_on()` / `turn_off()`                 | Power only           | Call `toggle_switch()` internally         |
| `turn_<state>_on()` / `turn_<state>_off()` | Named binary state   | `turn_child_lock_on()`                    |
| `toggle_<state>(bool)`                     | Toggle binary state  | `toggle_child_lock()`, `toggle_display()` |
| `set_<attribute>(value)`                   | Non-binary state     | `set_brightness()`, `set_fan_level()`     |

Base-class methods that not every device implements are stubs: `del` unused
args, `logger.debug()` whether the feature is unsupported or not configured,
`return False`. Concrete classes override them, and declare `__slots__ = ()`.

## Adding a new device

Only proceed with a packet capture for every request/response involved (rule 2).
A complete addition touches:

1. `device_map.py`: add a `*Map` entry to the right `*_modules` list.
2. `devices/vesync<type>.py`: add the class (mixin + base class), or reuse an
   existing class if the API is identical.
3. `models/<type>_models.py`: add request/response models for new payloads.
4. `src/tests/call_json_<type>.py`: add the `get_details()` response to
   `DETAILS_RESPONSES[setup_entry]`, plus any non-default `METHOD_RESPONSES`.
5. `src/tests/test_<type>.py`: add device-specific methods to `device_methods`
   if the device has methods beyond `base_methods`.
6. Run `PYTEST_CONFIRM=1 pytest src/tests/test_<type>.py --write_api` to record
   YAML fixtures, check them against the capture, then run `pytest` to confirm.
7. Docs: add a `:::` block for the class in `docs/devices/<type>.md`, and list
   the model in `docs/supported_devices.md` and the README device list.
8. In the PR, state that hardware testing (model + firmware) must be done by a
   human with the device.

New *features* on an existing device type: add state to the `DeviceState`
subclass and the method to the base class, then implement it in the concrete
class(es) that support it, gated by a `features` flag in the device map.

## Testing

Tests verify the exact API requests each device method sends. Summary below;
details in [src/tests/AGENTS.md](src/tests/AGENTS.md).

- **`TestBase`** (`base_test_cases.py`) patches `VeSync.async_call_api()`. Each
  call is captured (url, method, json_object, headers), scrubbed by
  `api_scrub()`, and compared with `src/tests/api/<module>/<setup_entry>.yaml`.
  Used by all `test_<type>.py` device tests.
- **`TestApiFunc`** patches `aiohttp.ClientSession` with `AiohttpMockSession`
  (`aiohttp_mocker.py`) to exercise the full HTTP cycle. Used for login and
  `async_call_api()` error handling (`test_x_vesync_login.py`,
  `test_x_vesync_api_responses.py`, which are current tests, not legacy).
- **Parametrization**: `conftest.py:pytest_generate_tests()` reads class
  attributes. `device = 'outlets'` makes it read `cls.outlets` (setup entries
  derived from `device_map.outlet_modules`); `base_methods` run on every device;
  `device_methods` maps a setup entry to extra methods. It generates
  `test_details` and `test_methods` with IDs like `outlets.ESW15-USA.['turn_on']`.
- **Fixtures**: a missing fixture fails the test. `--write_api` writes YAML only
  for methods that have none. Use `--write_api --overwrite` only when an
  existing request has genuinely changed, and review the YAML diff. Never edit
  fixtures by hand to make a test pass. In non-interactive shells these flags
  require `PYTEST_CONFIRM=1`, otherwise the run aborts.
- Response helpers live in `defaults.py` (`build_bypass_v1_response()`,
  `build_bypass_v2_response()`, `FunctionResponses*`). `xtest_x_*.py` files are
  legacy and not collected.
- Coverage gaps: thermostats and air fryers have no test module or YAML
  fixtures, and aren't registered in `call_json.ALL_DEVICE_MAP_MODULES`.

## Code style

Config: `ruff.toml`, `mypy.ini`, `.pylintrc`, `setup.cfg` (flake8). Ruff and the
pre-commit hooks apply to `src/pyvesync` only; `src/tests` is excluded.

- Ruff `select = ["ALL"]` with a short ignore list; line length 90; 4-space indent.
- Single quotes for strings, double quotes for docstrings.
- Google-style docstrings on all public classes, methods and functions
  (overridden methods may omit them).
- `from __future__ import annotations` at the top of every module; full type
  hints with `X | None` (never `Optional` / `Union`); type-only imports behind
  `if TYPE_CHECKING:`.
- Imports grouped: `__future__`, stdlib, third-party, local.
- Logging: `logger = logging.getLogger(__name__)` with `%s` arguments, never
  f-strings in log calls. f-strings elsewhere.
- `__slots__` on state classes, device classes and `VeSync`.
- Naming: PascalCase classes, snake_case functions/properties, UPPER_SNAKE_CASE
  constants, UPPER enum members.
- Match the surrounding code; do not reformat or refactor unrelated code.

## Git and PR workflow

- Branch from and target **`dev`**. `master` is release-only: merges there
  publish to PyPI and deploy docs.
- PR titles must use Conventional Commits (`feat:`, `fix:`, `docs:`,
  `refactor:`, `test:`, `chore:`), enforced by CI.
- Fill in `.github/PULL_REQUEST_TEMPLATE.md`, including the real-hardware section.
- Do not bump `version` in `pyproject.toml` in feature or fix PRs; that happens
  in the release PR to `master`.
- CI (`.github/workflows/RunTest.yaml`) runs ruff check, pylint and pytest on
  Python 3.11–3.14; mkdocs build runs only on PRs to `master`. mypy is not in
  CI. It runs through pre-commit and pre-commit.ci, so run it locally.

### Never commit

These are local or sensitive files. Stage specific paths instead of using
`git add -A`:

- `creds.json`, `.vesync_auth` (credentials and tokens)
- `*.log`, `models.json`, `tasks.md`, `tools/`
- `docs/superpowers/`, `docs/development/reviews/`
- `.claude/settings.local.json`, `.mcp.json`

Redact tokens, account IDs, emails and device identifiers from any log, capture
or `last_response` output before it goes into an issue, PR or fixture.
