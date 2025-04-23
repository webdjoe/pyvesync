# Documentation for Etekcity / Valceno Smart Bulbs

## Table of Contents

<!-- markdownlint-disable MD051 -->

See each device class for available attributes and methods:

- [BulbState Class](#pyvesync.base_devices.bulb_base.BulbState)
- [Etekcity Smart Bulb ESL100](#pyvesync.devices.vesyncbulb.VeSyncBulbESL100)
- [Etekcity Smart Bulb ESL100CW](#pyvesync.devices.vesyncbulb.VeSyncBulbESL100CW)
- [Etekcity Smart Bulb ESL100MC](#pyvesync.devices.vesyncbulb.VeSyncBulbESL100MC)
- [Valceno Smart Bulb ESL100MC](#pyvesync.devices.vesyncbulb.VeSyncBulbValcenoA19MC)
- [VeSyncBulb Abstract Base Class](#pyvesync.base_devices.bulb_base.VeSyncBulb)

::: pyvesync.base_devices.bulb_base.BulbState
    options:
        toc_label: "BulbState"
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: true

::: pyvesync.devices.vesyncbulb.VeSyncBulbESL100
    options:
        filters:
            - "!^_.*"
            - "__init__"
            - "!color*"
            - "!rgb*"
            - "!hsv*"
            - "!get_pid"
        summary:
            functions: false
        group_by_category: true
        show_root_heading: true
        toc_label: "Etekcity Dimmable ESL100"
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_signature_annotations: true
        signature_crossrefs: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: true

::: pyvesync.devices.vesyncbulb.VeSyncBulbESL100CW
    options:
        filters:
            - "!^_.*"
            - "__init__"
            - "!color*"
            - "!rgb*"
            - "!hsv*"
            - "!get_pid"
        summary:
            functions: false
        group_by_category: true
        show_root_heading: true
        toc_label: "Etekcity Tunable ESL100CW"
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_signature_annotations: true
        show_if_no_docstring: true
        signature_crossrefs: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: false
        merge_init_into_class: true

::: pyvesync.devices.vesyncbulb.VeSyncBulbESL100MC
    options:
        filters:
            - "!^_.*"
            - "__init__"
            - "!get_pid"
        summary:
            functions: false
        group_by_category: true
        toc_label: "Etekcity Multicolor ESL100MC"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_signature_annotations: true
        show_if_no_docstring: true
        signature_crossrefs: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: false
        merge_init_into_class: true

::: pyvesync.devices.vesyncbulb.VeSyncBulbValcenoA19MC
    options:
        filters:
            - "!^_.*"
            - "__init__"
            - "!get_pid"
        summary:
            functions: false
        group_by_category: true
        toc_label: "Valceno Multicolor Bulb"
        show_root_heading: true
        show_root_toc_entry: true
        show_category_heading: true
        show_source: true
        show_if_no_docstring: true
        inherited_members: true
        docstring_options:
            ignore_init_summary: false
        merge_init_into_class: true

::: pyvesync.base_devices.bulb_base.VeSyncBulb
    options:
        filters:
            - "!^_.*"
        summary:
            functions: false
        group_by_category: true
        show_root_heading: true
        show_root_toc_entry: true
        toc_label: "VeSyncBulb Base Class"
        show_category_heading: true
        show_source: true
        heading_level: 3
        inherited_members: true
        show_if_no_docstring: true
        docstring_options:
            ignore_init_summary: true
        merge_init_into_class: true
