# Documentation for Base Devices

This is the base device inherited by all device classes. This should *NOT* be instantiated directly.

All methods and attributes are available on all devices.

::: pyvesync.base_devices.vesyncbasedevice.VeSyncBaseToggleDevice
    handler: python
    options:
      group_by_category: true
      show_category_heading: true
      show_root_full_path: false
      show_root_heading: true
      show_source: true
      merge_init_into_class: true
      show_if_no_docstring: true
      show_signature_annotations: true
      inherited_members: true
      docstring_options:
            ignore_init_summary: true
      filters:
        - "!.*pid"
        - "!^__*"
        - "!displayJSON"

::: pyvesync.base_devices.vesyncbasedevice.VeSyncBaseDevice
    handler: python
    options:
      group_by_category: true
      show_category_heading: true
      show_root_full_path: false
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      merge_init_into_class: true
      show_if_no_docstring: true
      show_signature_annotations: true
      docstring_options:
        ignore_init_summary: false
      filters:
        - "!^__*"
        - "!displayJSON"

::: pyvesync.base_devices.vesyncbasedevice.DeviceState
    handler: python
    options:
      group_by_category: true
      show_root_full_path: false
      show_category_heading: true
      show_root_heading: true
      show_source: true
      merge_init_into_class: true
      show_if_no_docstring: true
      show_signature_annotations: true
      docstring_options:
        ignore_init_summary: false
      filters:
        - "!.*pid"
        - "!^__*"
