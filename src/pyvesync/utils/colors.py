"""Data structures for handling colors."""

from __future__ import annotations

import colorsys
import logging
from dataclasses import InitVar, dataclass

from pyvesync.utils.helpers import Validators

_LOGGER = logging.getLogger(__name__)


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

    def __str__(self) -> str:
        """Return string representation."""
        return f'RGB({self.red}, {self.green}, {self.blue})'

    def __repr__(self) -> str:
        """Return string representation."""
        return f'RGB(red={self.red}, green={self.green}, blue={self.blue})'

    def to_tuple(self) -> tuple[float, float, float]:
        """Return RGB values as tuple."""
        return self.red, self.green, self.blue

    def to_dict(self) -> dict[str, float]:
        """Return RGB values as dict."""
        return {
            'red': self.red,
            'green': self.green,
            'blue': self.blue,
        }


@dataclass
class HSV:
    """HSV color space dataclass, for internal use in `utils.colors.Color` dataclass.

    Does not perform any validation and should not be used directly, only
    by the `Color` dataclass through the Color.from_hsv(hue, saturation, value)
    classmethod or Color.rgb_to_hsv(red, green, blue) method.

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

    def __str__(self) -> str:
        """Return string representation."""
        return f'HSV({self.hue}, {self.saturation}, {self.value})'

    def __repr__(self) -> str:
        """Return string representation."""
        return f'HSV(hue={self.hue}, saturation={self.saturation}, value={self.value})'

    def to_tuple(self) -> tuple[float, float, float]:
        """Return HSV values as tuple."""
        return self.hue, self.saturation, self.value

    def to_dict(self) -> dict[str, float]:
        """Return HSV values as dict."""
        return {
            'hue': self.hue,
            'saturation': self.saturation,
            'value': self.value,
        }


@dataclass
class Color:
    """Dataclass for color values.

    This class should be instantiated through the `from_rgb` or `from_hsv`
    classmethods. It will return a `Color` object with the appropriate color
    values in RGB and HSV.

    Args:
        color_object (HSV | RGB): Named tuple with color values.

    Attributes:
        hsv (namedtuple): hue (0-360), saturation (0-100), value (0-100)
            see [`HSV dataclass`][pyvesync.utils.colors.HSV]
        rgb (namedtuple): red (0-255), green (0-255), blue (0-255)
            see [`RGB dataclass`][pyvesync.utils.colors.RGB]
    """

    color_object: InitVar[HSV | RGB]

    def __post_init__(
        self,
        color_object: HSV | RGB,
    ) -> None:
        """Check HSV or RGB Values and create named tuples."""
        if isinstance(color_object, HSV):
            self.hsv = color_object
            self.rgb = self.hsv_to_rgb(*self.hsv.to_tuple())
        elif isinstance(color_object, RGB):
            self.rgb = color_object
            self.hsv = self.rgb_to_hsv(*self.rgb.to_tuple())

    def __str__(self) -> str:
        """Return string representation."""
        return f'Color(hsv={self.hsv}, rgb={self.rgb})'

    def __repr__(self) -> str:
        """Return string representation."""
        return f'Color(hsv={self.hsv}, rgb={self.rgb})'

    def as_dict(self) -> dict[str, dict]:
        """Return color values as dict."""
        return {
            'hsv': {
                'hue': self.hsv.hue,
                'saturation': self.hsv.saturation,
                'value': self.hsv.value,
            },
            'rgb': {
                'red': self.rgb.red,
                'green': self.rgb.green,
                'blue': self.rgb.blue,
            },
        }

    @classmethod
    def from_rgb(
        cls, red: float | None, green: float | None, blue: float | None
    ) -> Color | None:
        """Create Color instance from RGB values.

        Args:
            red (NUMERIC_STRICT): The red component of the color,
                typically in the range [0, 255].
            green (NUMERIC_STRICT): The green component of the color,
                typically in the range [0, 255].
            blue (NUMERIC_STRICT): The blue component of the color,
                typically in the range [0, 255].

        Returns:
            Color | None: A Color object with the appropriate color values in RGB and HSV,
                or None if the input values are invalid.
        """
        if not Validators.validate_rgb(red, green, blue):
            _LOGGER.debug('Invalid RGB values')
            return None
        return cls(RGB(float(red), float(green), float(blue)))  # type: ignore[arg-type]

    @classmethod
    def from_hsv(
        cls, hue: float | None, saturation: float | None, value: float | None
    ) -> Color | None:
        """Create Color instance from HSV values.

        Args:
            hue (float): The hue component of the color,
                in the range [0, 360).
            saturation (float): The saturation component of the color,
                typically in the range [0, 1].
            value (float): The value (brightness) component of the color,
                typically in the range [0, 1].

        Returns:
            Color | None: A Color object with the appropriate color values in RGB and HSV,
                or None if the input values are invalid.
        """
        if not Validators.validate_hsv(hue, saturation, value):
            _LOGGER.debug('Invalid HSV values')
            return None
        return cls(
            HSV(float(hue), float(saturation), float(value))  # type: ignore[arg-type]
        )

    @staticmethod
    def hsv_to_rgb(hue: float, saturation: float, value: float) -> RGB:
        """Convert HSV to RGB.

        Args:
            hue (float): The hue component of the color, in the range [0, 360).
            saturation (float): The saturation component of the color,
                in the range [0, 1].
            value (float): The value (brightness) component of the color,
                in the range [0, 1].

        Returns:
            RGB: An RGB dataclass with red, green, and blue components.
        """
        return RGB(
            *tuple(
                round(i * 255, 0)
                for i in colorsys.hsv_to_rgb(hue / 360, saturation / 100, value / 100)
            )
        )

    @staticmethod
    def rgb_to_hsv(red: float, green: float, blue: float) -> HSV:
        """Convert RGB to HSV.

        Args:
            red (float): The red component of the color, in the range [0, 255].
            green (float): The green component of the color, in the range [0, 255].
            blue (float): The blue component of the color, in the range [0, 255].

        Returns:
            HSV: An HSV dataclass with hue, saturation, and value components.
        """
        hsv_tuple = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        hsv_factors = [360, 100, 100]

        return HSV(
            float(round(hsv_tuple[0] * hsv_factors[0], 2)),
            float(round(hsv_tuple[1] * hsv_factors[1], 2)),
            float(round(hsv_tuple[2] * hsv_factors[2], 0)),
        )
