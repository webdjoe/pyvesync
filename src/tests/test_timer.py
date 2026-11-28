"""Tests for the Timer helper."""

from unittest.mock import patch

from pyvesync.utils.helpers import Timer


def test_timer_starts_at_creation_time():
    """A timer created late in a process run starts from its creation time."""
    with patch("pyvesync.utils.helpers.time.time", return_value=1_000_000.0):
        timer = Timer(timer_duration=7200, action="off", remaining=7200)
    assert timer._update_time == 1_000_000

    with patch("pyvesync.utils.helpers.time.time", return_value=1_000_060.0):
        assert timer.time_remaining == 7140
        assert timer.running
