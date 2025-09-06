"""pytest test parametrization for VeSync devices."""


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
