"""Tests for the installed package and repository contract."""

from importlib.metadata import entry_points, requires

from packaging.requirements import Requirement


def test_console_scripts_are_registered() -> None:
    """A package installation exposes every supported command."""
    names = {item.name for item in entry_points(group="console_scripts")}

    assert {"hunchback-live", "hunchback-video", "hunchback-web"} <= names


def test_package_uses_one_opencv_distribution() -> None:
    """MediaPipe and the app must share one OpenCV installation."""
    dependency_names = {
        Requirement(item).name for item in (requires("hunchback-detection") or [])
    }

    assert "opencv-contrib-python" in dependency_names
    assert "opencv-python" not in dependency_names


def test_package_pins_legacy_mediapipe_api() -> None:
    """The pose engine depends on the MediaPipe solutions API."""
    dependencies = [
        Requirement(item) for item in (requires("hunchback-detection") or [])
    ]
    mediapipe = next(item for item in dependencies if item.name == "mediapipe")

    assert str(mediapipe.specifier) == "==0.10.21"
