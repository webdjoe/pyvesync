# Contributing to pyvesync

Contributions are welcome! Please follow the guidelines below to ensure a quick and smooth review process.

Uses the [pre-commit](https://pre-commit.com/) framework to manage and maintain code quality. This is automatically run on `commit` to check for formatting and linting issues by the `pre-commit.ci` service. Running this manually is not required, but recommended to ensure a clean commit:

```bash
    pre-commit run
```

**NOTE:** Changes must be staged in order for this to work properly.

## Code Style

### General Style Guidelines

- Single quotes for strings, except when the string contains a single quote or is a docstring.
- Use f-strings for string formatting.
- Use type hinting for function signatures and variable declarations.
- Docstrings for all public classes, methods and functions. Not required for inherited methods and properties.
- Constants should be stored in the `const` module, there should be no hardcoded strings or numbers in the code.
- Line length is limited to 90 characters.
- Classes and public variables must be camel cased.
- Local variables, methods and properties must be snake cased.
- Imports must be sorted and grouped by standard library, third party and local imports.

### Device Method and Attribute Naming

- All states specific to a device type must be stored in the `DeviceState` class in the base device type module. For example, `SwitchState` for switches, `PurifierState` for purifiers, etc.
- All device properties and methods are to be created in the specific device type base class, not in the implementation device class.
- All device methods that set one or the other binary state must be named `turn_<state>_on()` or `turn_<state>_off()`. For example, `turn_on()`, `turn_off()`, `turn_child_lock_on()`, `turn_child_lock_off()`.
- The `turn_on()` and `turn_off()` are specific methods that use the `toggle_switch()` method. Any method that toggles a binary state must be named `toggle_<state>()`. For example, `toggle_lock()`, `toggle_mute()`, `toggle_child_lock()`.
- Methods that set a specific state that is not on/off must be named `set_<state>()`. For example, `set_brightness()`, `set_color()`, `set_temperature()`.

## Testing and Linting

For convenience, the `tox` can be used to run tests and linting. This requires `tox` to be installed in your Python environment.

To run all tests and linting:

```bash
    tox
```

Specific test environments:

```bash
    tox -e py38          # Run tests with Python 3.8
    tox -e py39          # Run tests with Python 3.9
    tox -e py310         # Run tests with Python 3.10
    tox -e py311         # Run tests with Python 3.11
    tox -e lint          # Run pylint checks
    tox -e ruff          # Run ruff checks
    tox -e mypy          # Run mypy type checks
```

## Requests to Add Devices

Please see [CAPTURING.md](CAPTURING.md) for instructions on how to capture the necessary information to add a new device.
