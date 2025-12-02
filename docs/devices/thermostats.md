# VeSync Thermostats


::: pyvesync.devices.vesyncthermostat
    options:
        show_root_heading: true
        members: false
        members_order: source

::: pyvesync.base_devices.thermostat_base.ThermostatState
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"

::: pyvesync.base_devices.thermostat_base.VeSyncThermostat
    options:
        show_root_heading: true
        members_order: source
        filters:
            - "!^_.*"
