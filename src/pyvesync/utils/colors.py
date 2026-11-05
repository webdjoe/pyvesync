"""Data structures for handling colors."""

from __future__ import annotations

import colorsys
import logging
from dataclasses import InitVar, dataclass
from typing import ClassVar

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


class RGBNightlightColor:
    """Color helpers for RGB nightlight devices.

    Encapsulates the 8-color gradient used by the VeSync app for the RGB
    nightlight color slider, along with the geometry needed to map an
    arbitrary RGB color to a slider position and to apply or recover
    brightness.
    """

    # 8-color gradient used by VeSync app for RGB nightlight color slider
    GRADIENT: ClassVar[list[tuple[int, int, int]]] = [
        (252, 50, 0),  # #fc3200 - Red (position 0)
        (255, 171, 2),  # #ffab02 - Orange (position ~14.3)
        (181, 255, 0),  # #b5ff00 - Yellow-Green (position ~28.6)
        (2, 255, 120),  # #02ff78 - Green (position ~42.9)
        (3, 200, 254),  # #03c8fe - Cyan (position ~57.1)
        (0, 40, 255),  # #0028ff - Blue (position ~71.4)
        (220, 0, 255),  # #dc00ff - Purple (position ~85.7)
        (254, 0, 60),  # #fe003c - Pink/Red (position 100)
    ]

    @staticmethod
    def apply_brightness_to_rgb(
        red: int, green: int, blue: int, brightness: int
    ) -> tuple[int, int, int]:
        """Apply brightness to RGB color using HSV color space.

        The VeSync app applies brightness by converting to HSV, setting the V
        (value) component to brightness/100, then converting back to RGB.

        From decompiled app: yv/p.java method b()

        Args:
            red: Red value (0-255).
            green: Green value (0-255).
            blue: Blue value (0-255).
            brightness: Brightness level (0-100).

        Returns:
            tuple: Brightness-adjusted (red, green, blue) values.
        """
        if max(red, green, blue) == 0:
            return (0, 0, 0)
        h, s, _ = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
        v = brightness / 100.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (round(r * 255), round(g * 255), round(b * 255))

    @staticmethod
    def normalize_to_full_brightness(
        red: int, green: int, blue: int
    ) -> tuple[int, int, int]:
        """Normalize brightness-adjusted RGB back to full brightness (100%).

        Inverse of `apply_brightness_to_rgb`. Given RGB values that have been
        dimmed, recover the original "full brightness" color by setting HSV
        value to 1.0 while preserving hue and saturation.

        Args:
            red: Red value (0-255), brightness-adjusted.
            green: Green value (0-255), brightness-adjusted.
            blue: Blue value (0-255), brightness-adjusted.

        Returns:
            tuple: Normalized (red, green, blue) values at full brightness.
        """
        if max(red, green, blue) == 0:
            return (0, 0, 0)
        h, s, _ = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
        v = 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (round(r * 255), round(g * 255), round(b * 255))

    @classmethod
    def rgb_to_color_slider_location(cls, red: int, green: int, blue: int) -> int:
        """Convert RGB values to colorSliderLocation (0-100).

        The VeSync app uses an 8-color gradient for the color slider. This
        finds the closest position on that gradient by checking each segment
        and finding where the input color best fits.

        Note: Input RGB should be at full brightness for accurate results.
        If the input has reduced brightness, first normalize it.

        From decompiled app: yv/p.java (HumidifierColor.kt)

        Args:
            red: Red value (0-255).
            green: Green value (0-255).
            blue: Blue value (0-255).

        Returns:
            int: Color slider location (0-100).
        """
        gradient = cls.GRADIENT
        num_colors = len(gradient)
        segment_size = 100.0 / (num_colors - 1)

        best_position = 0.0
        best_distance_sq = float('inf')

        for i in range(num_colors - 1):
            ax, ay, az = gradient[i]
            bx, by, bz = gradient[i + 1]
            dx, dy, dz = bx - ax, by - ay, bz - az
            seg_len_sq = dx * dx + dy * dy + dz * dz
            if seg_len_sq == 0:
                fraction = 0.0
            else:
                fraction = (
                    (red - ax) * dx + (green - ay) * dy + (blue - az) * dz
                ) / seg_len_sq
                fraction = max(0.0, min(1.0, fraction))

            cx = ax + dx * fraction
            cy = ay + dy * fraction
            cz = az + dz * fraction
            distance_sq = (red - cx) ** 2 + (green - cy) ** 2 + (blue - cz) ** 2

            if distance_sq < best_distance_sq:
                best_distance_sq = distance_sq
                best_position = i * segment_size + fraction * segment_size

        return round(best_position)
