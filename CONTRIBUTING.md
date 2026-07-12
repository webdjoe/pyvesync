# Contributing to the pyvesync Library

## Contribution Rules

Every contribution — from humans and AI coding assistants alike — must follow
three rules. The full guide, including code style and the diagnostic information
to include with a request, is at
[docs/development/contributing.md](docs/development/contributing.md)
(published at
<https://webdjoe.github.io/pyvesync/latest/development/contributing>).

1. **Follow the intended architecture.** Add devices through the three-tier
   hierarchy (base class → concrete device + API mixin → device map), keep state
   in the device's `DeviceState` subclass, models in `models/`, and constants in
   `pyvesync.const`. API request/response shapes must come from a real packet
   capture — never invented.
2. **Verify on real hardware before merge.** New device support and any change
   to device behavior must be tested on the physical device, and the pull
   request must state the model and firmware version tested. Testing only through
   Home Assistant does not count.
3. **One change per pull request.** Each PR must be a single feature, fix, or
   edit. Large or mixed PRs will be asked to be broken up before review.

If you are using an AI assistant, point it at
[`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md); you remain responsible for
ensuring the result follows these rules.

## Setting up the Development Environment

1. Git clone the repository

```bash
git clone https://github.com/webdjoe/pyvesync && cd pyvesync
```

2. Create and activate a separate python virtual environment for pyvesync

```bash
# Check Python version is 3.11 or higher
python3 --version # or python --version or python3.11 --version
# Create a new venv
python3 -m venv pyvesync-venv
# Activate the venv
source pyvesync-venv/bin/activate
# or ....
pyvesync-venv\Scripts\activate.ps1 # on powershell
pyvesync-venv\Scripts\activate.bat # on command prompt

# Install development tools
pip install -e .[dev]
```

3. Make changes and test in virtual environment

If the above steps were executed successfully, you should now have:

- Code directory `pyvesync`(which we cloned from github)
- Python venv directory `pyvesync` (all the dependencies/libraries are contained here)

Any change in the code will now be directly reflected and can be tested. To deactivate the python venv, simply
run `deactivate`.

## Testing Python with Tox

Install tox, navigate to the pyvesync repository which contains the tox.ini file, and run tox as follows:

```bash
# Run all tests and linters
tox

# Run tests, linters separately
tox -e testenv # pytest
tox -e pylint # linting
tox -e lint # flake8 & pydocstrings
tox -e mypy # type checkings
```

Tests are run based off of the API calls recorded in the [api](src/tests/api) directory. Please read the [Test Readme](src/tests/README.md) for further details on the structure of the tests.

## Ensure new devices are Integrated in Tests

If you integrate a new device, please read the [testing README](src/tests/README.md) to ensure that your device is tested.

## Testing with pytest and Writing API to YAML

Part of the pytest test are against a library of API calls written to YAML files in the `tests` directory. If you are developing a new device, be aware that these tests will fail at first until you are ready to write the final API.

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
