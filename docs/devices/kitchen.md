# VeSync Air Fryers

Currently the only supported air fryer is the  Cosori 3.7 and 5.8 Quart Air Fryer. This device is a smart air fryer that can be monitored and controlled via this library.

::: pyvesync.devices.vesynckitchen
    options:
        show_root_heading: true
        members: false

::: pyvesync.devices.vesynckitchen.AirFryer158138State
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.devices.vesynckitchen.VeSyncAirFryer158
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.base_devices.fryer_base.FryerState
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.base_devices.fryer_base.VeSyncFryer
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"
