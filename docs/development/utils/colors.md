# Color Handlers

The `pyvesync.utils.colors` module provides classes and functions for handling color conversions and representations. It includes the `Color` class, which serves as a base for color manipulation, and the `HSV` and `RGB` classes for specific color models. The module is designed for internal use within the library and is not intended for public use.

## Color class

This is the primary class that holds the color data and provides methods for conversion between different color models (RGB, HSV). It also includes methods for validating color values and generating color strings in various formats.

::: pyvesync.utils.colors.Color
    handler: python
    options:
      show_root_heading: true
      show_source: true
      filters:
      - "!Config"
      - "!^__init*"
      - "!__post_init__"
      - "!__str__"

::: pyvesync.utils.colors.HSV
    handler: python
    options:
      show_root_heading: true
      show_source: true
      filters:
      - "!Config"
      - "!^__init*"
      - "!__post_init__"
      - "!__str__"

::: pyvesync.utils.colors.RGB
    handler: python
    options:
      show_root_heading: true
      show_source: true
      filters:
      - "!Config"
      - "!__post_init__"
      - "!__str__"
