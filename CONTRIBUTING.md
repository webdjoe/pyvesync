# Contributing to pyvesync

Thanks for your interest in improving pyvesync! This page covers the common path
from issue to merged pull request. The full guide, which covers code style,
architecture, testing internals and the release process, is published at
[webdjoe.github.io/pyvesync/latest/development/contributing](https://webdjoe.github.io/pyvesync/latest/development/contributing)
(source: [docs/development/contributing.md](docs/development/contributing.md)).

## Contribution rules

Every contribution, whether from a human or an AI coding assistant, must follow
these three rules. They are enforced through review and the pull request
checklist, so please self-attest honestly.

1. **Follow the intended architecture.** Add devices through the three-tier
   hierarchy (base class → concrete device + API mixin → device map). Keep state
   in the device type's `DeviceState` subclass, request/response models in
   `src/pyvesync/models/`, and constants in `pyvesync.const`. API
   request/response shapes must come from a real packet capture. Never invent
   them.
2. **Verify on real hardware before merge.** New device support and any change
   to device behavior must be tested on the physical device, and the pull
   request must state the model and firmware version tested. Testing only
   through Home Assistant does not count.
3. **One change per pull request.** Each PR must be a single feature, fix, or
   edit. Large or mixed PRs will be asked to be split before review.

> [!IMPORTANT]
> **Using an AI coding assistant?** Point it at [AGENTS.md](AGENTS.md) (and
> [src/tests/AGENTS.md](src/tests/AGENTS.md) for test work). You remain
> responsible for the result: it must follow the rules above, must not fabricate
> API fields, and must not be submitted without real-device testing.

## Before opening an issue

Use the issue templates. They ask for exactly the information maintainers need.

- **[Bug report](.github/ISSUE_TEMPLATE/bug-report.yml):** pyvesync and Python
  versions, device model and firmware, a minimal reproduction script, a redacted
  `DEBUG` log, and `device.last_response` for the failing call.
- **[Device request](.github/ISSUE_TEMPLATE/device-request.yml):** model number,
  `product_type`, firmware, region, a product page link, and how you will help
  verify the device. A packet capture or a temporarily shared device is
  required. See [Capturing](docs/development/capturing.md).

To capture a redacted debug log:

```python
async with VeSync('EMAIL', 'PASSWORD', redact=True) as manager:  # redact is the default
    manager.log_to_file('pyvesync.log', stdout=True)  # enables DEBUG logging
    await manager.login()
    await manager.update()
    device = manager.devices.outlets[0]
    await device.turn_off()
    print(device.last_response)
```

Check the log for anything sensitive before posting. Never post packet captures
publicly; the capturing guide explains how to share them privately.

## Development setup

Requires Python 3.11 or newer.

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/<your-username>/pyvesync.git
cd pyvesync
git remote add upstream https://github.com/webdjoe/pyvesync.git

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS
# .\venv\Scripts\Activate.ps1     # Windows PowerShell
# venv\Scripts\activate.bat       # Windows cmd

# Install the package in editable mode with dev tools
pip install -e .[dev]

# Install the pre-commit hooks (mypy, ruff check --fix, ruff format, file checks)
pre-commit install
```

## Workflow

1. **Branch from `dev`.** `dev` is the integration branch. `master` is
   release-only: every merge to it publishes to PyPI.

   ```bash
   git fetch upstream
   git switch -c fix/esw15-nightlight upstream/dev
   ```

2. **Make one focused change** that follows the architecture. For a new device,
   follow [Adding a new device](https://webdjoe.github.io/pyvesync/latest/development/contributing#adding-a-new-device).
3. **Add or update tests** and record API fixtures (see below).
4. **Run the checks locally** (see below).
5. **Update the docs** if you changed behavior or the public API. New devices
   also need entries in `docs/devices/`, `docs/supported_devices.md` and the
   README device list.
6. **Open a pull request into `dev`.** Fill in the
   [PR template](.github/PULL_REQUEST_TEMPLATE.md), including the real-hardware
   section. Do not bump the version in `pyproject.toml`; maintainers do that in
   the release PR.

### Pull request titles

PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/).
This is enforced by CI:

| Prefix      | Use for                       | Example                                       |
| ----------- | ----------------------------- | --------------------------------------------- |
| `feat:`     | New feature or device support | `feat: Add support for LAP-C601S purifier`    |
| `fix:`      | Bug fix                       | `fix: Handle token expiration during update`  |
| `docs:`     | Documentation only            | `docs: Clarify capturing steps`               |
| `refactor:` | No behavior change            | `refactor: Simplify bypass V2 result parsing` |
| `test:`     | Tests only                    | `test: Add fixtures for ESW10-USA`            |
| `chore:`    | Maintenance, dependencies, CI | `chore: Bump ruff`                            |

## Testing

Tests check the exact API request each device method sends against YAML fixtures
in `src/tests/api/`.

```bash
pytest                                  # full suite
pytest src/tests/test_outlets.py        # one module
pytest src/tests/test_outlets.py -k "ESW15-USA"   # one device
```

When you add a device or method, its fixture won't exist yet and the test will
fail until you record it:

```bash
pytest src/tests/test_outlets.py --write_api               # write missing fixtures only
pytest src/tests/test_outlets.py --write_api --overwrite   # rewrite fixtures (API changed)
```

These flags ask for confirmation. In a non-interactive shell, prefix the command
with `PYTEST_CONFIRM=1`. Always review the generated YAML against your packet
capture, and only use `--overwrite` when a request has intentionally changed.

See [src/tests/README.md](src/tests/README.md) and the
[testing docs](https://webdjoe.github.io/pyvesync/latest/development/testing)
for how tests are parametrized and how to add response data for a new device.

## Linting and type checking

```bash
pre-commit run --all-files    # what pre-commit.ci runs on every PR (stage changes first)

ruff check src/pyvesync       # lint
ruff format src/pyvesync      # format
mypy src/pyvesync             # type check
pylint src/pyvesync           # pylint
```

Or use tox (environments from `tox.ini`):

```bash
tox                 # all environments
tox -e 3.11         # pytest on Python 3.11 (also 3.12, 3.13, 3.14)
tox -e lint         # pylint
tox -e flake8       # flake8 + flake8-docstrings
tox -e mypy         # mypy
tox -e ruff         # ruff check
tox -e 3.12 -- src/tests/test_outlets.py --write_api   # pass pytest args after --
```

Code style in brief: ruff with all rules enabled, 90-character lines, single
quotes, Google-style docstrings, full type hints. The
[full guide](https://webdjoe.github.io/pyvesync/latest/development/contributing#code-style)
has the details.

## What CI checks

On every pull request to `dev` or `master`:

- **Run Linting and Unit Tests:** `ruff check`, `pylint`, and `pytest` on
  Python 3.11, 3.12, 3.13 and 3.14. The MkDocs build also runs on PRs to `master`.
- **pre-commit.ci:** the pre-commit hooks, including **mypy** (mypy is not part
  of the test workflow, so run it locally).
- **Semantic Title:** the Conventional Commits PR title check.

## Getting help

Open an issue on GitHub. For questions about a specific device, include the
diagnostics listed above.
