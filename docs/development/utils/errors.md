# Errors and Exceptions

The `pyvesync` library parses the code provided in the API response to determine if the request was successful and a possible reason for failure.

::: pyvesync.utils.errors
    handler: python
    options:
      toc_label: "errors Module"
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false
      members: false
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.ResponseInfo
    handler: python
    options:
      parameter_headings: true
      toc_label: "ResponseInfo Class"
      show_root_heading: true
      heading_level: 2
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.ErrorTypes
    handler: python
    options:
      parameter_headings: true
      toc_label: "ErrorTypes StrEnum"
      show_root_heading: true
      heading_level: 2
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.ErrorCodes
    handler: python
    options:
      parameter_headings: true
      toc_label: "BypassV2Mixin Class"
      show_root_heading: true
      heading_level: 2
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.raise_api_errors
    handler: python
    options:
      parameter_headings: true
      show_root_heading: true
      heading_level: 2
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

## VeSync Exceptions

::: pyvesync.utils.errors.VeSyncError
    handler: python
    options:
      parameter_headings: true
      toc_label: "VeSyncError"
      show_root_heading: true
      heading_level: 3
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.VesyncLoginError
    handler: python
    options:
      parameter_headings: true
      show_root_heading: true
      heading_level: 3
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.VeSyncTokenError
    handler: python
    options:
      parameter_headings: true
      show_root_heading: true
      heading_level: 3
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.VeSyncServerError
    handler: python
    options:
      parameter_headings: true
      show_root_heading: true
      heading_level: 3
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.VeSyncRateLimitError
    handler: python
    options:
      parameter_headings: true
      show_root_heading: true
      heading_level: 3
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.VeSyncAPIResponseError
    handler: python
    options:
      parameter_headings: true
      show_root_heading: true
      heading_level: 3
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"

::: pyvesync.utils.errors.VeSyncAPIStatusCodeError
    handler: python
    options:
      parameter_headings: true
      show_root_heading: true
      heading_level: 3
      show_source: true
      filters:
        - "!.*pid"
        - "!^__*"
