"""Tests for the per-device `setup_entry` parametrization in conftest.py."""

import pytest

WIDGETS = ["WIDGET-A", "WIDGET-B"]


class TestSetupEntryGenerator:
    """A class with a `device` attribute gets per-device `setup_entry` tests."""

    device = "widgets"
    widgets = WIDGETS

    def test_runs_once_per_device(self, request, setup_entry):
        """An unmarked `setup_entry` test runs on each device, with an ID per device."""
        assert setup_entry in WIDGETS
        assert request.node.callspec.id == f"widgets.{setup_entry}"

    @pytest.mark.parametrize("setup_entry", ["WIDGET-A"])
    def test_own_parametrize_is_kept(self, request, setup_entry):
        """A test that parametrizes `setup_entry` itself is left alone."""
        assert request.node.callspec.id == "WIDGET-A"

    @pytest.mark.parametrize(("setup_entry", "value"), [("WIDGET-B", 1)])
    def test_own_tuple_parametrize_is_kept(self, setup_entry, value):
        """Tuple-style argnames are recognised too."""
        assert (setup_entry, value) == ("WIDGET-B", 1)
