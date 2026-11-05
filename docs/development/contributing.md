# Contributing to pyvesync

Contributions are welcome! This is the complete contribution guide. Following
it keeps review quick and smooth. A shorter summary lives in the repository's
[CONTRIBUTING.md](https://github.com/webdjoe/pyvesync/blob/dev/CONTRIBUTING.md).

## Contribution Rules

These three rules are the foundation of a mergeable contribution. They apply to
everyone, and **especially** to changes generated with the help of an AI coding
assistant. They are enforced through review and the pull request checklist, not
CI, so please self-attest honestly.

### 1. Follow the intended architecture

pyvesync uses a deliberate three-tier device hierarchy. New work must fit into
it rather than working around it:

1. **Base classes** (`src/pyvesync/base_devices/`): an abstract base per device
   type. Device state lives in the `DeviceState` subclass of the relevant base
   (`OutletState`, `PurifierState`, etc.), and device methods/properties belong
   on the device-type base class, not the concrete implementation class.
2. **Concrete devices** (`src/pyvesync/devices/`): a specific model, implemented
   by combining an API mixin (`BypassV1Mixin` or `BypassV2Mixin`) with the base
   class.
3. **Device map** (`src/pyvesync/device_map.py`): maps the API's device-type
   string to the class, features, and config.

Additional non-negotiables:

- API request/response models go in `src/pyvesync/models/`.
- Constants, modes, and default values go in `pyvesync.const`, with no hardcoded
  strings or magic numbers in device code.
- **Never fabricate API request/response fields.** They must come from a real
  packet capture (see [Capturing](./capturing.md)). If no capture exists for the
  behavior, the work cannot be completed or merged.

### 2. Verify on real hardware before merge

**New device support and any change to device behavior must be tested on the
physical device before it is merged.** This is a hard requirement.

- The pull request must state the **model and firmware version** it was tested
  against.
- Testing only through Home Assistant (or another downstream integration) does
  **not** satisfy this requirement. You need a script or session that exercises
  the library directly against the device.
- If you do not own the device, provide a packet capture and/or share the device
  with a maintainer (see [Capturing](./capturing.md)) so it can be verified
  before merge.

### 3. One change per pull request

Each pull request must be a **single** feature, fix, or edit. Split large or
mixed changes into separate PRs.

- Do not bundle unrelated changes (e.g. a new device plus a refactor plus a docs
  overhaul) into one PR.
- Small, focused PRs are reviewable and verifiable. Large speculative PRs that
  touch many devices at once will be asked to be broken up before review.

## Working with AI Coding Assistants

AI assistants (Claude Code, Codex, Cursor, Copilot, etc.) are welcome tools, but
the human opening the PR is responsible for the result. The repository includes
agent instructions that most assistants load automatically:

- [`AGENTS.md`](https://github.com/webdjoe/pyvesync/blob/dev/AGENTS.md) covers
  the rules, architecture, commands, and workflow.
- [`src/tests/AGENTS.md`](https://github.com/webdjoe/pyvesync/blob/dev/src/tests/AGENTS.md)
  covers the test suite layout, fixtures, and common test tasks.
- `CLAUDE.md` and `src/tests/CLAUDE.md` import the AGENTS.md files for Claude
  Code. Codex and most other tools read AGENTS.md directly. If you edit agent
  guidance, edit AGENTS.md.

When driving an assistant against this repository:

- Require it to follow the three Contribution Rules above.
- Add new devices by mapping them in `device_map.py` and subclassing the correct
  base class plus API mixin, not with ad-hoc, one-off code.
- Do not let it invent API request/response shapes. If there is no packet
  capture for a behavior, it cannot be implemented.
- Do not submit device code that has not been run on the physical device.
- Keep each PR to a single change. Do not batch a session's worth of speculative
  edits into one large PR.
- Provide the diagnostic information described below.

## Diagnostic Information to Include

Provide the following when requesting a device, proposing a feature, or reporting
a bug. The GitHub issue templates (**Bug Report** and **Device Request**) prompt
for these fields. For packet-capture instructions, see [Capturing](./capturing.md).

**Requesting a new device:**

- Device model number and `product_type`
- Firmware version
- Region / country code
- Link to the product page
- A packet capture, or a stated willingness to share the device with a maintainer

**Adding a new feature:**

- The target device model(s) the feature was tested on, with firmware version
- The relevant captured API request and response for the new behavior
- A redacted `DEBUG` log of the library exercising the feature

**Reporting a bug / troubleshooting:**

- pyvesync version and Python version
- Device model and firmware version
- A redacted `DEBUG` log
- The `device.last_response` output for the failing call
- A minimal reproduction script

### Capturing a redacted DEBUG log

`log_to_file()` sets the `pyvesync` logger to `DEBUG` and attaches a file
handler in one call. Keep `redact=True` (the default) so tokens, account IDs,
emails and device identifiers are replaced with `##_REDACTED_##`:

```python
import asyncio
from pyvesync import VeSync


async def main():
    async with VeSync('EMAIL', 'PASSWORD', redact=True) as manager:
        manager.log_to_file('pyvesync.log', stdout=True)
        await manager.login()
        await manager.update()

        device = manager.devices.outlets[0]
        await device.turn_off()
        print(device.last_response)  # result of the last API call


asyncio.run(main())
```

Set `LibraryLogger.verbose = True` (from `pyvesync.utils.logs`) to include full
request and response bodies. See [Logging](./utils/logging.md) for more options.
Review the log before posting it, and never post packet captures publicly.

## Getting Started

### Install the Development Environment

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/pyvesync.git
cd pyvesync
git remote add upstream https://github.com/webdjoe/pyvesync.git

# Create a virtual environment (Python 3.11+)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\Activate.ps1  # Windows PowerShell

# Install with dev dependencies
pip install -e .[dev]
```

### Pre-commit Hooks

The project uses [pre-commit](https://pre-commit.com/) to enforce code quality on
every commit. The [pre-commit.ci](https://pre-commit.ci/) service also runs these
checks automatically on pull requests. The hooks apply to `src/pyvesync` only.

The hooks include:

- **check-yaml** / **check-toml** / **check-ast**: validate file syntax
- **trailing-whitespace** / **end-of-file-fixer**: whitespace cleanup
- **mypy**: static type checking
- **ruff-check**: linting with auto-fix
- **ruff-format**: code formatting

To install and run pre-commit locally:

```bash
pre-commit install      # Install hooks (runs on every git commit)
pre-commit run          # Run on staged files only
pre-commit run --all-files  # Run on all files
```

/// note
Changes must be staged (`git add`) before running `pre-commit run` for it to
check the correct files.
///

## Development Workflow

1. **Branch from `dev`.** `dev` is the integration branch that all pull
   requests target. `master` is the release branch, and every merge to it
   publishes a release.

    ```bash
    git fetch upstream
    git switch -c feat/lap-c601s upstream/dev
    ```

2. **Make a single, focused change** that follows the architecture rules.
3. **Add or update tests** and record API fixtures (see
   [Testing and Linting](#testing-and-linting)).
4. **Run the linters, type checker, and tests locally.**
5. **Update documentation** when behavior or the public API changes (see
   [Documentation](#documentation)).
6. **Open a pull request into `dev`** with a Conventional Commits title and the
   pull request template filled in, including the real-hardware verification
   section.

/// note
Do not change the version in `pyproject.toml` in a feature or fix PR. The
version is bumped in the release PR from `dev` to `master`.
///

## Adding a New Device

Only start once you have a packet capture covering every request and response
the device needs (see [Capturing](./capturing.md)).

1. **Device map:** add a `*Map` entry (`OutletMap`, `PurifierMap`, ...) to the
   matching `*_modules` list in `device_map.py`. Set `dev_types` to the model
   strings the API returns, along with `class_name`, `setup_entry`,
   `model_name`, `model_display`, and `features` (enums from `pyvesync.const`).
   Add any type-specific options such as modes or fan levels.
2. **Device class:** if an existing class already speaks the device's API,
   point the map entry at it. Otherwise add a class in
   `src/pyvesync/devices/vesync<type>.py`, combining the API mixin with the
   base class (`class VeSyncNewPlug(BypassV2Mixin, VeSyncOutlet)`), and model it
   on the closest existing device.
3. **Models:** add request/response dataclasses for new payloads in
   `src/pyvesync/models/<type>_models.py`. Field names match the API's JSON keys.
4. **State and features:** new state belongs in the type's `DeviceState`
   subclass. New public methods belong on the base class and are gated by a
   feature flag in the device map.
5. **Test responses:** add the device's `get_details()` response to
   `DETAILS_RESPONSES` in `src/tests/call_json_<type>.py`, plus any
   method-specific responses in `METHOD_RESPONSES`.
6. **Test methods:** add device-specific methods to `device_methods` in
   `src/tests/test_<type>.py`.
7. **Fixtures:** record the requests with `pytest --write_api`, check the YAML
   against the capture, and rerun `pytest` without flags.
8. **Docs:** add a `:::` block for the class in `docs/devices/<type>.md`, and
   list the model in `docs/supported_devices.md` and the README device list.
9. **Verify on hardware** and state the model and firmware in the PR.

## Pull Request Process

### Semantic PR Titles

Pull request titles must follow the
[Conventional Commits](https://www.conventionalcommits.org/) format. This is
enforced by the **Semantic Title** GitHub Action on all PRs. Valid prefixes:

- `feat:`: new feature or device support
- `fix:`: bug fix
- `docs:`: documentation changes
- `refactor:`: code refactoring (no functional change)
- `test:`: adding or updating tests
- `chore:`: maintenance, dependency updates, CI changes

Examples:

```text
feat: Add support for LAP-C601S air purifier
fix: Handle token expiration during device update
docs: Update contributing guidelines
```

### What Happens on a PR

When you open a pull request targeting `dev` or `master`, the **Run Linting and
Unit Tests** workflow runs:

1. **Ruff**: `ruff check --output-format=github src/pyvesync`
2. **Pylint**: `pylint src/pyvesync`
3. **Pytest**: the full test suite on Python 3.11, 3.12, 3.13, and 3.14
4. **MkDocs build**: only on PRs to `master` (Python 3.12)

The workflow fails if any of these steps fail. Separately:

- **pre-commit.ci** runs the pre-commit hooks, including **mypy**. mypy is
  not part of the test workflow, so run it locally.
- **Semantic Title** checks the PR title.

A maintainer then reviews the change against the Contribution Rules and the PR
checklist.

## Code Style

### Ruff Configuration

The project uses [ruff](https://docs.astral.sh/ruff/) as the primary linter and
formatter. The configuration is in `ruff.toml` with the following key settings:

- **Line length**: 90 characters
- **Indent**: 4 spaces
- **Rule selection**: `ALL` (all rules enabled, with specific ignores)
- **Docstring convention**: Google style
- **Quote style**: single quotes (double quotes for docstrings)
- **Scope**: `src/pyvesync`. The `src/tests` directory is excluded from ruff
  and pre-commit.

Ruff runs with auto-fix enabled in pre-commit, so many issues are corrected
automatically on commit. mypy (`mypy.ini`), pylint (`.pylintrc`) and flake8
(`setup.cfg`) use the same 90-character limit.

### General Style Guidelines

- **Quotes**: Single quotes for all strings. Double quotes for docstrings.

    ```python
    name = 'my_device'            # Single quotes
    msg = "it's a device"         # Double quotes when string contains single quote

    def update(self):
        """Update device state."""  # Double quotes for docstrings
    ```

- **String formatting**: Use f-strings, except in logging calls, which use
  `%s` arguments.

    ```python
    logger.debug('Device %s status: %s', self.device_name, status)  # logging uses %s
    message = f'Device {self.device_name} updated'  # f-strings elsewhere
    ```

- **Type hints**: Required for all function signatures. Use `|` union syntax, not `Union` or `Optional`. Use `from __future__ import annotations` at the top of every module.

    ```python
    from __future__ import annotations

    def set_brightness(self, brightness: int) -> bool: ...
    def get_config(self) -> OutletMap | None: ...
    async def call_api(self, data: dict | None = None) -> dict | None: ...
    ```

- **TYPE_CHECKING imports**: Imports used only for type hints should be guarded behind `if TYPE_CHECKING:` to avoid circular imports at runtime.

    ```python
    from __future__ import annotations
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from pyvesync import VeSync
        from pyvesync.device_map import OutletMap
    ```

- **Import ordering**: Imports are grouped and sorted by: (1) `__future__`, (2) standard library, (3) third-party, (4) local imports. Each group is separated by a blank line.

    ```python
    from __future__ import annotations

    import logging
    from typing import TYPE_CHECKING

    from mashumaro.mixins.orjson import DataClassORJSONMixin

    from pyvesync.base_devices.outlet_base import VeSyncOutlet
    from pyvesync.const import DeviceStatus, ConnectionStatus
    ```

- **Docstrings**: Required for all public classes, methods, and functions. Use Google-style format. Not required for inherited/overridden methods.

    ```python
    class OutletState(DeviceState):
        """Base state class for Outlets.

        This class holds all of the state information for the outlet devices.

        Args:
            device (VeSyncOutlet): The device object.
            details (ResponseDeviceDetailsModel): The device details.
            feature_map (OutletMap): The feature map for the device.

        Attributes:
            energy (float): Energy usage in kWh.
            power (float): Power usage in Watts.
            voltage (float): Voltage in Volts.

        Note:
            Not all attributes are available on all devices.
        """
    ```

- **Line length**: 90 characters maximum.

- **Naming conventions**:

    | Element             | Convention                      | Example                                |
    | ------------------- | ------------------------------- | -------------------------------------- |
    | Classes             | PascalCase                      | `VeSyncOutlet7A`, `OutletState`        |
    | Methods / functions | snake_case                      | `turn_on()`, `set_brightness()`        |
    | Properties          | snake_case                      | `device_status`, `fan_level`           |
    | Constants           | UPPER_SNAKE_CASE                | `DEFAULT_TZ`, `STATUS_OK`              |
    | Enums               | PascalCase class, UPPER members | `DeviceStatus.ON`                      |
    | Module-level logger | `logger` (preferred)            | `logger = logging.getLogger(__name__)` |

- **Constants**: All constants, default values, and device modes must be defined in the `pyvesync.const` module. No hardcoded strings or magic numbers in device code. Use `StrEnum` or `IntEnum` for enum values.

    ```python
    # In const.py
    class DeviceStatus(StrEnum):
        ON = 'on'
        OFF = 'off'

    # In device code - use the enum, not the raw string
    self.state.device_status = DeviceStatus.ON  # correct
    self.state.device_status = 'on'             # incorrect
    ```

- **`__slots__`**: Used on state classes, device classes, and the `VeSync`
  manager class to restrict attribute creation and improve memory usage.

### Device Method and Attribute Naming

- All states specific to a device type must be stored in the `DeviceState` subclass in the base device type module. For example, `SwitchState` for switches, `PurifierState` for purifiers, etc.
- All device properties and methods are to be created in the specific device type base class, not in the implementation device class.
- Binary state methods follow this naming pattern:

    | Pattern                                    | Usage                | Example                                         |
    | ------------------------------------------ | -------------------- | ----------------------------------------------- |
    | `turn_on()` / `turn_off()`                 | Power on/off         | Inherited from `VeSyncBaseToggleDevice`         |
    | `turn_<state>_on()` / `turn_<state>_off()` | Named binary state   | `turn_child_lock_on()`, `turn_child_lock_off()` |
    | `toggle_<state>(bool)`                     | Toggle binary state  | `toggle_child_lock()`, `toggle_display()`       |
    | `set_<attribute>(value)`                   | Set non-binary state | `set_brightness()`, `set_fan_level()`           |

- The `turn_on()` and `turn_off()` methods are specific to power and call the `toggle_switch()` method internally.
- Base-class methods that a concrete device may not implement use a stub
  pattern. They discard unused arguments with `del`, log at debug level whether
  the feature is unsupported or just not configured, and return `False`.
  Concrete classes that support the feature override the method.

    ```python
    async def set_nightlight_state(self, mode: str) -> bool:
        """Set nightlight mode."""
        del mode  # unused
        if not self.supports_nightlight:
            logger.debug('Device does not support nightlight.')
        else:
            logger.debug('Nightlight mode not configured for %s', self.device_name)
        return False
    ```

- Concrete device classes declare `__slots__ = ()`.

### Models Directory

Data model files in `pyvesync/models/` have relaxed naming rules (`N803`, `N804`,
`N802`, `N815` ignored) because model field names must match the VeSync API's
JSON keys exactly (e.g., `traceId`, `accountID`, `configModule`). Request models
subclass `RequestBaseModel` and response models subclass `ResponseBaseModel`
from `models/base_models.py`.

## Testing and Linting

### Running Tests Locally

```bash
# Run all tests
pytest

# Run a specific test file
pytest src/tests/test_outlets.py

# Run the tests for one device
pytest src/tests/test_outlets.py -k "ESW15-USA"
```

### Recording API Fixtures

Device tests compare each request the library sends with a YAML fixture in
`src/tests/api/<device module>/<setup_entry>.yaml`. A missing fixture makes the
test **fail**, so new devices and methods need their fixtures recorded:

```bash
# Write fixtures that don't exist yet (existing fixtures are untouched)
pytest src/tests/test_outlets.py --write_api

# Rewrite existing fixtures - only when a request has intentionally changed
pytest src/tests/test_outlets.py --write_api --overwrite
```

Both flags ask for confirmation before writing. In a non-interactive shell (CI,
scripts, AI agents) set `PYTEST_CONFIRM=1` to skip the prompt, otherwise the run
aborts. Narrow these runs to the module you changed, and review the YAML diff
before committing. Never edit fixtures by hand or overwrite them just to make a
failing test pass.

### Running with Tox

For convenience, `tox` can be used to run tests and linting. This requires `tox` to be installed in your Python environment.

```bash
# Run all environments
tox

# Specific environments
tox -e 3.11          # Run tests with Python 3.11
tox -e 3.12          # Run tests with Python 3.12
tox -e 3.13          # Run tests with Python 3.13
tox -e lint          # Run pylint checks
tox -e flake8        # Run flake8 checks
tox -e ruff          # Run ruff checks
tox -e mypy          # Run mypy type checks

# Pass arguments to pytest after --
tox -e 3.12 -- src/tests/test_outlets.py --write_api
```

### Running Linters Directly

```bash
ruff check src/pyvesync          # Lint
ruff format src/pyvesync         # Format
mypy src/pyvesync                # Type check
pylint src/pyvesync              # Pylint
```

See the [Testing](./testing.md) documentation and the
[tests README](https://github.com/webdjoe/pyvesync/blob/dev/src/tests/README.md)
for details on the test architecture, fixtures, and adding tests for new devices.

## Documentation

The documentation site is built with [MkDocs](https://www.mkdocs.org/) and
[mkdocstrings](https://mkdocstrings.github.io/). Most API reference pages are
generated from docstrings, which is why public classes and methods need complete
Google-style docstrings.

```bash
pip install -e .[docs]
mkdocs serve      # live preview at http://127.0.0.1:8000
mkdocs build      # what CI runs on PRs to master
```

- Device pages live in `docs/devices/<type>.md`. Each device class is rendered by
  a `::: pyvesync.devices.<module>.<ClassName>` block. Copy the options from a
  neighbouring block.
- New devices are also listed in `docs/supported_devices.md` and the README.
- Navigation is defined in `mkdocs.yml`.

## Release Process

Releases are triggered automatically when code is merged to `master`. The **Release and Publish** workflow:

1. **Extracts the version** from `pyproject.toml`
2. **Validates** the new version is greater than the latest git tag
3. **Builds** the distribution package (`python -m build`)
4. **Creates a GitHub Release** with auto-generated release notes and the version as the tag (e.g., `3.4.1`)
5. **Publishes to PyPI** via the `pypa/gh-action-pypi-publish` action
6. **Deploys documentation** using `mike` to GitHub Pages, updating the `latest` alias

### Versioning

The project version is defined in `pyproject.toml` under `[project].version`. The version follows [semantic versioning](https://semver.org/):

- **Major** (x.0.0) - Breaking changes
- **Minor** (0.x.0) - New features, new device support
- **Patch** (0.0.x) - Bug fixes

When preparing a release PR to `master`, bump the version in `pyproject.toml`. The release workflow will fail if the new version is not greater than the previous tag.

### Documentation Deployment

Documentation is built with MkDocs and deployed to GitHub Pages using
[mike](https://github.com/jimporter/mike) for version management. Each release
creates a versioned deployment and updates the `latest` alias. The documentation
site is at
[webdjoe.github.io/pyvesync/latest](https://webdjoe.github.io/pyvesync/latest/).

## Dependency Management

[Dependabot](https://docs.github.com/en/code-security/dependabot) is configured to check for updates weekly to both pip dependencies and GitHub Actions versions.

## Requests to Add Devices

Please see [Capturing](./capturing.md) for instructions on how to capture the
information needed to add a new device, or how to share a device with a
maintainer instead.
