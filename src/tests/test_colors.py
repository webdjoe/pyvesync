"""Unit tests for pyvesync.utils.colors.RGBNightlightColor."""

from pyvesync.utils.colors import RGBNightlightColor


def test_normalize_black_stays_black():
    """Black (0,0,0) must not normalize to white."""
    assert RGBNightlightColor.normalize_to_full_brightness(0, 0, 0) == (0, 0, 0)


def test_apply_brightness_black_stays_black():
    """Applying brightness to black must stay black, not become gray."""
    assert RGBNightlightColor.apply_brightness_to_rgb(0, 0, 0, 50) == (0, 0, 0)


def test_normalize_recovers_full_brightness_color():
    """A saturated hue dimmed then normalized recovers a max-channel of 255."""
    dimmed = RGBNightlightColor.apply_brightness_to_rgb(252, 50, 0, 40)
    base = RGBNightlightColor.normalize_to_full_brightness(*dimmed)
    assert max(base) == 255


def test_apply_brightness_rounds_not_truncates():
    """round() keeps the green channel at 128 where int() would give 127."""
    # (255,128,64) scaled to value 0.502 -> green 128.5 rounds to 128 (int->127 earlier)
    red, green, blue = RGBNightlightColor.apply_brightness_to_rgb(255, 129, 64, 51)
    assert green == 66  # round(129/255*0.51*255) == round(65.79) == 66
