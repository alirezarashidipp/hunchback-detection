"""Tests for CLI imports, validation, and resource cleanup."""

import importlib
from pathlib import Path

import numpy as np
import pytest


def test_cli_module_imports_without_loading_optional_runtime() -> None:
    """Help and package discovery work before OpenCV is loaded."""
    module = importlib.import_module("hunchback_detection.video_stream")

    assert callable(module.run_video_cli)


def test_run_video_rejects_missing_input_before_loading_opencv(tmp_path: Path) -> None:
    """A missing path receives an actionable file error."""
    from hunchback_detection.video_stream import run_video

    missing = tmp_path / "missing.mp4"

    with pytest.raises(FileNotFoundError, match="missing.mp4"):
        run_video(str(missing))


class FakeCapture:
    def __init__(self) -> None:
        self.released = False

    def read(self) -> tuple[bool, np.ndarray]:
        return True, np.zeros((4, 4, 3), dtype=np.uint8)

    def release(self) -> None:
        self.released = True


class FailingDetector:
    def __init__(self) -> None:
        self.closed = False

    def analyze(self, frame: np.ndarray, threshold: float) -> None:
        raise RuntimeError("analysis failed")

    def close(self) -> None:
        self.closed = True


class FakeCV:
    def __init__(self) -> None:
        self.windows_closed = False

    def destroyAllWindows(self) -> None:
        self.windows_closed = True


def test_run_stream_releases_resources_when_analysis_fails() -> None:
    """Capture, detector, and window resources close on processing errors."""
    from hunchback_detection.video_stream import run_stream

    capture = FakeCapture()
    detector = FailingDetector()
    cv_module = FakeCV()

    with pytest.raises(RuntimeError, match="analysis failed"):
        run_stream(capture, detector=detector, cv_module=cv_module)

    assert capture.released is True
    assert detector.closed is True
    assert cv_module.windows_closed is True


def test_run_stream_preserves_cap_keyword_compatibility() -> None:
    """Existing callers may continue to pass the capture as ``cap``."""
    from hunchback_detection.video_stream import run_stream

    capture = FakeCapture()
    detector = FailingDetector()

    with pytest.raises(RuntimeError, match="analysis failed"):
        run_stream(cap=capture, detector=detector, cv_module=FakeCV())

    assert capture.released is True
