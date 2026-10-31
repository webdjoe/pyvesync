# VeSync Air Fryers

The supported air fryers are the Cosori 3.7 and 5.8 Quart Air Fryer and the Cosori Turbo Tower Pro Smart dual-chamber Air Fryer. These devices can be monitored and controlled via this library.

Programs prepared on the Turbo Tower Pro through the API must still be started with the Start button on the appliance.

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

::: pyvesync.devices.vesynckitchen.AirFryerDC111State
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.devices.vesynckitchen.FryerChamberState
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.devices.vesynckitchen.VeSyncAirFryerDC111
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
