# Contributing to pyvesync

Contributions are welcome! Please follow the guidelines below to ensure a quick and smooth review process.

## Getting Started

### Install the Development Environment

```bash
# Clone the repository
git clone https://github.com/webdjoe/pyvesync.git
cd pyvesync

# Create a virtual environment (Python 3.11+)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate.ps1  # Windows PowerShell

# Install with dev dependencies
pip install -e .[dev]
```

### Pre-commit Hooks

The project uses [pre-commit](https://pre-commit.com/) to enforce code quality on every commit. The [pre-commit.ci](https://pre-commit.ci/) service also runs these checks automatically on pull requests.

The hooks include:

- **check-yaml** / **check-toml** / **check-ast** - Validates file syntax
- **trailing-whitespace** / **end-of-file-fixer** - Whitespace cleanup
- **mypy** - Static type checking
- **ruff-check** - Linting with auto-fix
- **ruff-format** - Code formatting

To install and run pre-commit locally:

```bash
pre-commit install      # Install hooks (runs on every git commit)
pre-commit run          # Run on staged files only
pre-commit run --all-files  # Run on all files
```

/// note
Changes must be staged (`git add`) before running `pre-commit run` for it to check the correct files.
///

## Pull Request Process

### Semantic PR Titles

Pull request titles must follow the [Conventional Commits](https://www.conventionalcommits.org/) format. This is enforced by a GitHub Action on all PRs. Valid prefixes:

- `feat:` - New feature or device support
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring (no functional change)
- `test:` - Adding or updating tests
- `chore:` - Maintenance, dependency updates, CI changes

Examples:

```text
feat: Add support for LAP-C601S air purifier
fix: Handle token expiration during device update
docs: Update contributing guidelines
```

### What Happens on a PR

When you open a pull request targeting `master` or `dev`, the **Run Linting and Unit Tests** workflow runs automatically:

1. **Ruff** - Lints the codebase with `ruff check --output-format=github`
2. **Pylint** - Runs pylint on `src/pyvesync`
3. **Pytest** - Runs the full test suite across Python 3.11, 3.12, and 3.13
4. **MkDocs Build** - Builds the documentation (only on PRs to `master`, Python 3.12)

All four checks must pass for the PR to be merged.

## Code Style

### Ruff Configuration

The project uses [ruff](https://docs.astral.sh/ruff/) as the primary linter and formatter. The configuration is in `ruff.toml` with the following key settings:

- **Line length**: 90 characters
- **Indent**: 4 spaces
- **Rule selection**: `ALL` (all rules enabled, with specific ignores)
- **Docstring convention**: Google style
- **Quote style**: Single quotes (double quotes for docstrings)

Ruff runs with auto-fix enabled in pre-commit, so many issues are corrected automatically on commit.

### General Style Guidelines

- **Quotes**: Single quotes for all strings. Double quotes for docstrings.

    ```python
    name = 'my_device'            # Single quotes
    msg = "it's a device"         # Double quotes when string contains single quote

    def update(self):
        """Update device state."""  # Double quotes for docstrings
    ```

- **String formatting**: Use f-strings.

    ```python
    logger.debug('Device %s status: %s', self.device_name, status)  # logging uses %s
    message = f'Device {self.device_name} updated'  # f-strings elsewhere
    ```

- **Type hints**: Required for all function signatures. Use `|` union syntax (Python 3.10+), not `Union` or `Optional`. Use `from __future__ import annotations` at the top of every module.

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
    | Module-level logger | `logger`                        | `logger = logging.getLogger(__name__)` |

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

- **`__slots__`**: Used on state classes and the `VeSync` manager class to restrict attribute creation and improve memory usage.

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

### Models Directory

Data model files in `pyvesync/models/` have relaxed naming rules (`N803`, `N804`, `N802`, `N815` ignored) because model field names must match the VeSync API's JSON keys exactly (e.g., `traceId`, `accountID`, `configModule`).

## Testing and Linting

### Running Tests Locally

```bash
# Run all tests
pytest

# Run a specific test file
pytest src/tests/test_outlets.py

# Write API fixtures for new devices
pytest --write_api
pytest --write_api --overwrite  # Overwrite existing fixtures
```

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
```

### Running Linters Directly

```bash
ruff check src/pyvesync          # Lint
ruff format src/pyvesync         # Format
mypy src/pyvesync                # Type check
pylint src/pyvesync              # Pylint
```

See the [Testing](./testing.md) documentation for details on the test architecture, fixtures, and adding tests for new devices.

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

Documentation is built with MkDocs and deployed to GitHub Pages using [mike](https://github.com/jimporter/mike) for version management. Each release creates a versioned deployment and updates the `latest` alias. The documentation site is at [pyvesync.github.io](https://pyvesync.github.io/).

## Dependency Management

[Dependabot](https://docs.github.com/en/code-security/dependabot) is configured to check for updates weekly to both pip dependencies and GitHub Actions versions.

## Requests to Add Devices

Please see [Capturing](./capturing.md) for instructions on how to capture the necessary information to add a new device.
