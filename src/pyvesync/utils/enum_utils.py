"""Utilities to handle Enums."""

from __future__ import annotations

import enum


class IntEnumMixin(enum.IntEnum):
    """Mixin class to handle missing enum values.

    Adds __missing__ method using the `extend_enum` function to
    return a new enum member with the name "UNKNOWN" and the
    missing value.
    """

    @classmethod
    def _missing_(cls: type[enum.IntEnum], value: object) -> enum.IntEnum:
        """Handle missing enum values by returning member with UNKNOWN name."""
        for member in cls:
            if member.value == value:
                return member
        unknown_enum_val = int.__new__(cls, value)  # type: ignore[call-overload]
        unknown_enum_val._name_ = 'UNKNOWN'
        unknown_enum_val._value_ = value  # type: ignore[assignment]
        unknown_enum_val.__objclass__ = cls.__class__  # type: ignore[assignment]
        return unknown_enum_val
