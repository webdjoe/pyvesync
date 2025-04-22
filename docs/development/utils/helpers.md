# helpers module

The `pyvesync.utils.helpers` module contains utility functions and classes that assist with various tasks within the library. These include converting values, processing states, and managing timers. The module is designed for internal use within the library and is not intended for public use.

## Timer class

::: pyvesync.utils.helpers.Timer
    handler: python
    options:
      members:
        - update
      show_root_heading: true
      show_source: true

## Helper class

Contains common methods and attributes used by other pyvesync modules.

::: pyvesync.utils.helpers.Helpers
    handler: python
    options:
      show_root_heading: true
      show_category_heading: true
      show_root_toc_entry: true
      members_order: "source"
      inherited_members: false
      show_source: true
      filters:
      - "!Config"
      - "!^__.*"
      - "!^_.*"
      - "!req_body"

## Validators Class

Contains common method to validate numerical values.

::: pyvesync.utils.helpers.Validators
    handler: python
    options:
      show_root_heading: true
      show_category_heading: true
      show_root_toc_entry: true
      inherited_members: false
      show_source: true
      filters:
      - "!Config"
      - "!^__.*"
      - "!^_.*"
