"""Data structures for handling colors."""

from __future__ import annotations
from dataclasses import InitVar, dataclass

import colorsys
from pyvesync.helper_utils.helpers import _LOGGER, Validators, NUMERIC_STRICT


@dataclass
class RGB:
    """RGB color space dataclass, for internal use in `utils.colors.Color` dataclass.

    Does not perform any validation, it should not be used directly. Used as an
    attribute in the :obj:`pyvesync.helpers.Color` dataclass. This should only be
    used through the :obj:`Color` dataclass with the Color.from_rgb(red, green, blue)
    classmethod.

    Attributes:
        red (float): The red component of the RGB color.
        green (float): The green component of the RGB color.
        blue (float): The blue component of the RGB color.
    """

    red: float
    green: float
    blue: float

    def __post_init__(self) -> None:
        """Convert to int."""
        self.red = int(self.red)
        self.green = int(self.green)
        self.blue = int(self.blue)

    def as_tuple(self) -> tuple[float, float, float]:
        """Return RGB values as tuple."""
        return self.red, self.green, self.blue


@dataclass
class HSV:
    """HSV color space dataclass, for internal use in `utils.colors.Color` dataclass.

    Does not perform any validation and should not be used directly, only
    by the `Color` dataclass through the Color.from_hsv(hue, saturation, value)
    classmethod.

    Attributes:
        hue (float): The hue component of the color, typically in the range [0, 360).
        saturation (float): The saturation component of the color,
            typically in the range [0, 1].
        value (float): The value (brightness) component of the color,
            typically in the range [0, 1].
    """
    hue: float
    saturation: float
    value: float

    def __post_init__(self) -> None:
        """Convert to int."""
        self.hue = int(self.hue)
        self.saturation = int(self.saturation)
        self.value = int(self.value)

    def as_tuple(self) -> tuple[float, float, float]:
        """Return HSV values as tuple."""
        return self.hue, self.saturation, self.value


@dataclass
class Color:
    """Dataclass for color values.

    For HSV, pass hue as value in degrees 0-360, saturation and value as values
    between 0 and 100. For RGB, pass red, green and blue as values between 0 and 255. This
    dataclass provides validation and conversion methods for both HSV and RGB color spaces

    Notes:
        To instantiate pass kw arguments for colors with *either* **hue, saturation and
        value** *or* **red, green and blue**. RGB will take precedence if both are
        provided. Once instantiated, the named tuples `hsv` and `rgb` will be
        available as attributes.

    Args:
        red (int): Red value of RGB color, 0-255
        green (int): Green value of RGB color, 0-255
        blue (int): Blue value of RGB color, 0-255
        hue (int): Hue value of HSV color, 0-360
        saturation (int): Saturation value of HSV color, 0-100
        value (int): Value (brightness) value of HSV color, 0-100

    Attributes:
        hsv (namedtuple): hue (0-360), saturation (0-100), value (0-100)
            see [`HSV dataclass`][pyvesync.helpers.HSV]
        rgb (namedtuple): red (0-255), green (0-255), blue (0-255)
            see [`RGB dataclass`][pyvesync.helpers.RGB]
    """
    color_object: InitVar[HSV | RGB]

    def __post_init__(
        self,
        color_object: HSV | RGB,
    ) -> None:
        """Check HSV or RGB Values and create named tuples."""
        if isinstance(color_object, HSV):
            self.hsv = color_object
            self.rgb = self.hsv_to_rgb(*self.hsv.as_tuple())
        elif isinstance(color_object, RGB):
            self.rgb = color_object
            self.hsv = self.rgb_to_hsv(*self.rgb.as_tuple())

    @classmethod
    def from_rgb(cls, red: NUMERIC_STRICT, green: NUMERIC_STRICT,
                 blue: NUMERIC_STRICT) -> Color | None:
        """Create Color instance from RGB values."""
        if not Validators.validate_rgb(red, green, blue):
            _LOGGER.debug("Invalid RGB values")
            return None
        return cls(RGB(float(red), float(green), float(blue)))

    @classmethod
    def from_hsv(cls, hue: NUMERIC_STRICT, saturation: NUMERIC_STRICT,
                 value: NUMERIC_STRICT) -> Color | None:
        """Create Color instance from HSV values."""
        if not Validators.validate_hsv(hue, saturation, value):
            _LOGGER.debug("Invalid HSV values")
            return None
        return cls(HSV(float(hue), float(saturation), float(value)))

    @staticmethod
    def hsv_to_rgb(hue: float, saturation: float, value: float) -> RGB:
        """Convert HSV to RGB."""
        return RGB(
            *tuple(round(i * 255, 0) for i in colorsys.hsv_to_rgb(
                hue / 360,
                saturation / 100,
                value / 100
            ))
        )

    @staticmethod
    def rgb_to_hsv(red: float, green: float, blue: float) -> HSV:
        """Convert RGB to HSV."""
        hsv_tuple = colorsys.rgb_to_hsv(
                red / 255,
                green / 255,
                blue / 255
            )
        hsv_factors = [360, 100, 100]

        return HSV(
            float(round(hsv_tuple[0] * hsv_factors[0], 2)),
            float(round(hsv_tuple[1] * hsv_factors[1], 2)),
            float(round(hsv_tuple[2] * hsv_factors[2], 0)),
        )
