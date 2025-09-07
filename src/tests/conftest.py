"""pytest test parametrization for VeSync devices."""
import os
import sys
import pytest


def pytest_addoption(parser):
    """Prevent new API's from being written during pipeline tests."""
    parser.addoption(
        "--write_api",
        action="store_true",
        default=False,
        help="run tests without writing API to yaml",
    )
    parser.addoption(
        "--overwrite",
        action="store_true",
        default=False,
        help="overwrite existing API in yaml - WARNING do not use unless absolutely necessary",
    )


def pytest_generate_tests(metafunc):
    """Generate tests for device methods.

    Excludes legacy tests that start with 'test_x'.
    """
    if metafunc.cls is None or 'test_x' in metafunc.module.__name__:
        return
    write_api = bool(metafunc.config.getoption('--write_api'))

    overwrite = bool(metafunc.config.getoption('--overwrite'))

    metafunc.cls.overwrite = overwrite
    metafunc.cls.write_api = write_api

    # Require class attribute 'device' to parametrize tests
    if 'device' in metafunc.cls.__dict__:
        device = metafunc.cls.__dict__['device']
        if device not in metafunc.cls.__dict__:
            return
        devices = metafunc.cls.__dict__[device]

        if metafunc.function.__name__ == 'test_details':
            return details_generator(metafunc, device, devices)

        if metafunc.function.__name__ == 'test_methods':
            return method_generator(metafunc, device, devices)


def details_generator(metafunc, gen_type, devices):
    """Parametrize device tests for get_details()."""
    id_list = []
    argvalues = []
    for setup_entry in devices:
        id_list.append(f"{gen_type}.{setup_entry}.update")
        argvalues.append([setup_entry, 'update'])
    metafunc.parametrize("setup_entry, method", argvalues, ids=id_list)


def method_generator(metafunc, gen_type, devices):
    """Parametrize device tests for methods."""
    if 'base_methods' in metafunc.cls.__dict__:
        base_methods = metafunc.cls.__dict__['base_methods']
    else:
        base_methods = []
    call_dict = {dt: base_methods.copy() for dt in devices}
    if 'device_methods' in metafunc.cls.__dict__:
        dev_methods = metafunc.cls.__dict__['device_methods']
        for dev in call_dict:
            if dev in dev_methods:
                call_dict[dev].extend(dev_methods[dev])
    id_list = []
    argvalues = []
    for dev, methods in call_dict.items():
        for method in methods:
            id_list.append(f'{gen_type}.{dev}.{method}')
            argvalues.append([dev, method])
    metafunc.parametrize("setup_entry, method", argvalues, ids=id_list)
    return


def _is_interactive(config: pytest.Config) -> bool:
    """Best-effort check for an interactive terminal."""
    tr = config.pluginmanager.getplugin("terminalreporter")
    if tr and getattr(tr, "isatty", False):
        return True
    for stream in (sys.__stdin__, sys.__stdout__, sys.__stderr__):
        try:
            if stream and stream.isatty():
                return True
        except Exception:
            pass
    return False


def _prompt_confirm(config: pytest.Config) -> bool:
    """Suspend capture, show a prompt, and return True if user confirmed."""
    flags = []
    if config.getoption("--write_api"):
        flags.append("--write_api")
    if config.getoption("--overwrite"):
        flags.append("--overwrite")

    if len(flags) == 0:
        return True

    if '--overwrite' in flags and '--write_api' not in flags:
        # Overwrite requires write_api to be set
        pytest.exit(
            "\nBoth --overwrite and --write_api need to be set to overwrite API calls.", 1
        )

    # Interactive prompt
    if "--write_api" in flags and "--overwrite" not in flags:
        msg = (
            "\nAre you sure you want to write API requests to files?\n"
            "Continue? [y/N]: "
        )
    elif "--overwrite" in flags and "--write_api" in flags:
        msg = (
            "\nAre you sure you want to OVERWRITE existing API requests?\n"
            "Continue? [y/N]: "
        )
    else:
        pytest.exit("\nUnrecognized combination of flags: " + ", ".join(flags), 1)

    if not flags:
        return True
    capman = config.pluginmanager.getplugin("capturemanager")
    tr = config.pluginmanager.getplugin("terminalreporter")
    if capman:
        # allow stdin/stdout to pass through for input()
        capman.suspend_global_capture(in_=True)  # type: ignore[arg-type]
    try:
        if tr and getattr(tr, "isatty", False):
            tr._tw.write(msg)   # type: ignore[arg-type]
        else:
            print(msg, end="", flush=True)
        try:
            resp = input().strip().lower()
        except EOFError:
            resp = ""
        return resp in {"y", "yes"}
    finally:
        if capman:
            capman.resume_global_capture()  # type: ignore[arg-type]


def _require_confirmation(config: pytest.Config) -> None:
    """Prompt once per session if any destructive flags are set."""
    if not config.getoption("--write_api") and not config.getoption("--overwrite"):
        return

    # Allow opt-out via flag or env var in CI
    if str(os.environ.get("PYTEST_CONFIRM", "")).lower() in {"1", "true", "yes", "y"}:
        return

    # If there's no TTY, force explicit opt-out instead of hanging
    if not _is_interactive(config):
        raise pytest.UsageError(
            "write_api require confirmation, but the session is non-interactive. "
            "Re-run with environment variable set PYTEST_CONFIRM=1."
        )

    if not _prompt_confirm(config):
        pytest.exit("Aborted by user.", returncode=1)


def pytest_sessionstart(session: pytest.Session) -> None:
    # Runs before collection; safe place to ask once and abort if needed
    _require_confirmation(session.config)
