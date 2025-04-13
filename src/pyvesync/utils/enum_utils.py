"""Utilities to handle Enums."""

from __future__ import annotations
from typing import TypeVar
import enum

T = TypeVar("T", bound=enum.Enum)


def extend_enum(
    enumeration: type[enum.Enum], name: str, value: object
) -> IntEnumMixin:
    """Add a new member to an existing Enum - adapted from ethanfurman/aenum ."""
    # pylint: disable=protected-access
    if name in enumeration.__dict__ or name in enumeration._member_map_:
        raise TypeError(
            f"{name} already used as {enumeration.__dict__.get(name, enumeration[name])}"
        )
    descriptor = None
    for base in enumeration.__mro__[1:]:
        descriptor = base.__dict__.get(name)
        if descriptor is not None:
            raise TypeError(f"{name} already in use in superclass {base.__name__}")
    try:
        _member_type_ = enumeration._member_type_  # type: ignore[attr-defined]
    except AttributeError as exc:
        raise TypeError(f"{enumeration} is not a supported Enum") from exc

    mt_new = _member_type_.__new__
    _new = (
        getattr(enumeration, "_new_member_", None)
        or getattr(enumeration, "__new_member__", None)
        or mt_new
    )
    new_member = _new(enumeration)
    if not hasattr(new_member, "_value_"):
        new_member._value_ = value
    value = new_member._value_
    new_member._name_ = name
    new_member.__objclass__ = enumeration.__class__
    return new_member


class IntEnumMixin(enum.Enum):
    """Mixin class to handle missing enum values.

    Adds __missing__ method using the `extend_enum` function to
    return a new enum member with the name "UNKNOWN" and the
    missing value.
    """

    @classmethod
    def _missing_(cls, value: object) -> enum.Enum:
        """Handle missing enum values by returning member with UNKNOWN name."""
        return extend_enum(cls, "UNKNOWN", value)
