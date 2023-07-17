def pytest_addoption(parser):
    """Prevent new API's from being written during pipeline tests."""
    parser.addoption(
        "--write_api", action="store_true", default=False,
          help="run tests without writing API to yaml"
    )
    parser.addoption(
        "--overwrite", action="store_true", default=False,
          help="overwrite existing API in yaml - WARNING do not use unless absolutely necessary"
    )

def pytest_generate_tests(metafunc):
    if metafunc.cls is None or 'test_x' in metafunc.module.__name__:
        return
    if metafunc.config.getoption('--write_api'):
        write_api = True
    else:
        write_api = False
    if metafunc.config.getoption('--overwrite'):
        overwrite = True
    else:
        overwrite = False
    metafunc.cls.overwrite = overwrite
    metafunc.cls.write_api = write_api
    if 'device' in metafunc.cls.__dict__:
        device = metafunc.cls.__dict__['device']
        if device not in metafunc.cls.__dict__:
            return
        devices = metafunc.cls.__dict__[device]
        if metafunc.function.__name__ == 'test_details':
            return details_generator(metafunc, device, devices)

        elif metafunc.function.__name__ == 'test_methods':
            return method_generator(metafunc, device, devices)


def details_generator(metafunc, gen_type, devices):
    """Parametrize device tests for get_details()."""
    id_list = []
    argvalues = []
    for dev_type in devices:
        id_list.append(f"{gen_type}.{dev_type}.update")
        argvalues.append([dev_type, 'update'])
    metafunc.parametrize("dev_type, method", argvalues, ids=id_list)
    return


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
    metafunc.parametrize("dev_type, method", argvalues, ids=id_list)
    return