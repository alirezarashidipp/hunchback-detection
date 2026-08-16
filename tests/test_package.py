"""Tests for the installed package and repository contract."""

from importlib.metadata import entry_points


def test_console_scripts_are_registered() -> None:
    """A package installation exposes every supported command."""
    names = {item.name for item in entry_points(group="console_scripts")}

    assert {"hunchback-live", "hunchback-video", "hunchback-web"} <= names
