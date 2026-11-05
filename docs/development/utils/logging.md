# Logging

The pyvesync library uses Python's standard `logging` module with the logger name `pyvesync`. The `LibraryLogger` class in `pyvesync.utils.logs` provides structured logging with automatic context (module and class name) and helper methods for API call logging.

::: pyvesync.utils.logs.LibraryLogger
    handler: python
    options:
      show_root_heading: true
      group_by_category: true
      show_category_heading: true
      show_source: false
      filters:
        - "!^_.*"
      merge_init_into_class: true
      show_signature_annotations: true

## Enabling Debug Logging

Debug mode is controlled by the level of the `pyvesync` logger. Set it to `DEBUG` with Python's logging module, or call `manager.log_to_file()` (see below), which sets the level for you:

```python
import logging
from pyvesync import VeSync

# Set the pyvesync logger level to DEBUG
logging.getLogger("pyvesync").setLevel(logging.DEBUG)
logging.basicConfig()  # Send log records to the console

async with VeSync(username="EMAIL", password="PASSWORD") as manager:
    await manager.login()
    print(manager.debug)  # True - reflects the pyvesync logger level
```

`manager.debug` is a read-only property. It reports whether debug logging is active and cannot be assigned to. The library caches the logger level and refreshes it before every API call, so changing the level takes effect on the next request.

## Logging to a File

For verbose debugging, the manager provides a helper to log to a file:

```python
async with VeSync(username="EMAIL", password="PASSWORD") as manager:
    manager.log_to_file("debug.log", stdout=True)
    # stdout=True will also print to the console
```

## Redacting Sensitive Information

By default, the library redacts sensitive information (tokens, account IDs) from log output. This can be controlled via the `redact` parameter on the `VeSync` constructor or the `redact` property:

```python
# Redaction is enabled by default
async with VeSync(username="EMAIL", password="PASSWORD", redact=True) as manager:
    manager.redact = False  # Disable redaction for debugging
```
