# VeSync Air Purifiers

## Contents:

- [PurifierState Class][pyvesync.base_devices.purifier_base.PurifierState]
- [VeSyncAirBypass Purifiers][pyvesync.devices.vesyncpurifier.VeSyncAirBypass] - Most common model
- [VeSyncAirBaseV2 Purifiers][pyvesync.devices.vesyncpurifier.VeSyncAirBaseV2] - Newer models
- [VeSyncAirSprout Purifiers][pyvesync.devices.vesyncpurifier.VeSyncAirSprout] - Sprout models
- [VeSyncAirVitalPetPro Purifiers][pyvesync.devices.vesyncpurifier.VeSyncAirVitalPetPro] - Vital Pet Pro
- [VeSyncAir131 Purifiers][pyvesync.devices.vesyncpurifier.VeSyncAir131] - PUR-LV131S Purifiers
- [VeSyncAirRH131 Purifiers][pyvesync.devices.vesyncpurifier.VeSyncAirRH131] - LV-RH131S Purifiers
- [VeSyncPurifier Base Device][pyvesync.base_devices.purifier_base.VeSyncPurifier] - Abstract base class

::: pyvesync.base_devices.purifier_base.PurifierState
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "PurifierState"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false

::: pyvesync.devices.vesyncpurifier.VeSyncAirBypass
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "VeSyncAirBypass Purifiers"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false

::: pyvesync.devices.vesyncpurifier.VeSyncAirBaseV2
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "VeSyncAirBaseV2 Purifiers"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false

::: pyvesync.devices.vesyncpurifier.VeSyncAirSprout
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "VeSyncAirSprout Purifiers"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false

## Vital Pet Pro

The Vital Pet Pro (LAP-P501S) has no `auto` work mode. Its Auto mode is one of
three auto mode types, defined in `pyvesync.const.PurifierAutoModeTypes` and
listed for the device in `purifier.auto_mode_types`:

| `PurifierAutoModeTypes` member | Value | App setting |
| --- | --- | --- |
| `ODOR_SHIELD_QUIET` | `odorShieldQuiet` | Auto, Quiet |
| `ODOR_SHIELD_BALANCED` | `odorShieldBalanced` | Auto, Balanced |
| `ODOR_SHIELD_PERFORMANCE` | `odorShieldPerformance` | Auto, Performance |

- `state.mode` is `auto` for all three, and `state.auto_mode_type` holds the
  type the device reports.
- `set_auto_mode_type()` switches to Auto with the given type.
- `set_mode('auto')` and `set_auto_mode()` send the last known type, or
  `ODOR_SHIELD_BALANCED` if none is known yet. The VeSync app's Auto button
  does the same.

```python
from pyvesync.const import PurifierAutoModeTypes

await purifier.set_auto_mode_type(PurifierAutoModeTypes.ODOR_SHIELD_QUIET)
await purifier.set_auto_mode()       # Auto, last known type (else Balanced)
await purifier.turn_on_auto_clean()  # start a pre-filter self-cleaning run
await purifier.turn_off_buzzer()     # mute the button beep
```

`state.auto_clean_status` is True while a self-cleaning run is active, and
`state.auto_clean_remaining` holds the seconds left. Timers can only turn the
purifier off.

::: pyvesync.devices.vesyncpurifier.VeSyncAirVitalPetPro
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "VeSyncAirVitalPetPro Purifiers"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false

::: pyvesync.devices.vesyncpurifier.VeSyncAir131
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "VeSyncAir131 Purifiers"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false

::: pyvesync.devices.vesyncpurifier.VeSyncAirRH131
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "VeSyncAirRH131"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false

::: pyvesync.base_devices.purifier_base.VeSyncPurifier
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        toc_label: "VeSyncPurifier Base Device"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: false
