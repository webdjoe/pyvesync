# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pyvesync is an async Python library for managing VeSync smart home devices (outlets, switches, fans, purifiers, humidifiers, bulbs, air fryers, thermostats). Uses aiohttp for network requests and mashumaro/orjson for serialization. Python 3.11+.

## Contribution Rules (READ FIRST)

Authoritative source: [docs/development/contributing.md](docs/development/contributing.md). These rules are mandatory for any change you propose or PR you help open:

1. **Follow the intended architecture.** Use the three-tier hierarchy described below — device state in the base `DeviceState` subclass, device methods on the device-type base class, models in `models/`, constants in `pyvesync.const`. Do not hardcode strings or magic numbers.
2. **Never fabricate API request/response fields.** Every request/response shape must come from a real packet capture (see [docs/development/capturing.md](docs/development/capturing.md)). If no capture exists for a behavior, you cannot implement it — say so instead of guessing.
3. **Real-hardware verification is required before merge.** New device support and any device-behavior change must be tested on the physical device, and the PR must state the model + firmware. You cannot verify hardware yourself — do not claim a device works; flag that a human with the device must test it.
4. **One change per PR.** Produce a single feature, fix, or edit per branch/PR. Do not batch unrelated changes or a whole session of speculative edits into one large PR — split them.
5. **Provide diagnostic info.** When adding a device/feature or diagnosing a bug, include the diagnostics listed in contributing.md (model, `product_type`, firmware, region, pyvesync/Python version, redacted `DEBUG` log, `device.last_response`).

If a request would violate these rules (e.g. "add support for device X" with no capture and no hardware to test), do not produce speculative code — explain the blocker and what is needed.

## Commands

```bash
# Install dev environment
pip install -e .[dev]

# Run all tests
pytest

# Run specific test file
pytest src/tests/test_outlets.py

# Run with tox (all environments)
tox

# Individual tox environments
tox -e testenv    # pytest
tox -e pylint     # pylint
tox -e lint       # flake8 + pydocstrings
tox -e mypy       # type checking
tox -e ruff       # ruff linting

# Lint and format
ruff check src/pyvesync
ruff format src/pyvesync
mypy src/pyvesync
pre-commit run --all-files

# Write API fixtures for new devices
pytest --write_api
pytest --write_api --overwrite  # overwrite existing fixtures
```

## Architecture

### Three-tier device hierarchy

1. **Base classes** (`src/pyvesync/base_devices/`) - Abstract base classes per device type. `VeSyncBaseDevice` (ABC, Generic) is the root. Each base defines a `DeviceState` subclass holding device-specific state.

2. **Concrete devices** (`src/pyvesync/devices/`) - Implement specific device models by combining a base class with an API mixin:

   ```python
   class VeSyncBulbESL100(BypassV1Mixin, VeSyncBulb):  # Bypass V1 API
   class VeSyncBulbESL100MC(BypassV2Mixin, VeSyncBulb):  # Bypass V2 API
   ```

3. **Device map** (`src/pyvesync/device_map.py`) - Maps device type strings from the API to their class, features, and config. Each product type has a `*Map` dataclass (OutletMap, BulbMap, etc.) and a `*_modules` list.

### Key modules

- `vesync.py` - Main `VeSync` manager class (async context manager, login, device management)
- `models/` - mashumaro dataclasses for API request/response serialization
- `utils/device_mixins.py` - `BypassV1Mixin` and `BypassV2Mixin` for API communication patterns
- `utils/errors.py` - Custom exceptions (`VeSyncError`, `VeSyncTokenError`, etc.)
- `device_container.py` - `DeviceContainer` (MutableSet) with typed accessors (`.outlets`, `.bulbs`, etc.)

### Adding a new device

1. Add device type mapping to the appropriate `*_modules` list in `device_map.py`
2. Create device class in `devices/` inheriting from base + mixin (BypassV1Mixin or BypassV2Mixin)
3. Add request/response models in `models/`
4. Add tests and write API fixtures with `pytest --write_api`

## Testing

Tests use pytest with parametrized fixtures. Two base test classes in `src/tests/base_test_cases.py`:

- `TestBase` - Mocks `call_api()`, uses YAML API fixtures from `src/tests/api/`
- `TestApiFunc` - Mocks `ClientSession` directly

Test classes define `device`, `base_methods`, and `device_methods` class attributes that drive parametrized test generation via `conftest.py`.

## Code Style

- Ruff with `select = ["ALL"]` (line-length 90, single quotes, Google docstrings)
- Pre-commit hooks: mypy, ruff-check, ruff-format
- Models directory has relaxed naming rules (N803, N804, N802, N815 ignored)
