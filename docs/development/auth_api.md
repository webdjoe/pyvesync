# Documentation for `pyvesync.auth` module

This module handles the authentication logic for the VeSync API. It is stored as the `auth` instance attribute of the `VeSync` class.

::: pyvesync.auth.VeSyncAuth
    handler: python
    options:
      group_by_category: true
      show_root_heading: true
      show_category_heading: true
      show_source: false
      filters:
        - "!.*_dev_test"
        - "!set_dev_id"
        - "!process_devices"
        - "!remove_old_devices"
        - "!device_time_check"
      merge_init_into_class: true
      show_signature_annotations: true
