"""Tests for CLI imports, validation, and resource cleanup."""

import importlib
import sys
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


class RecordingCapture:
    def __init__(
        self,
        frames: list[np.ndarray] | None = None,
        *,
        opened: bool = True,
        fps: float = 25.0,
    ) -> None:
        self.frames = list(frames or [])
        self.opened = opened
        self.fps = fps
        self.released = False

    def read(self) -> tuple[bool, np.ndarray]:
        if not self.frames:
            return False, np.empty((0, 0, 3), dtype=np.uint8)
        return True, self.frames.pop(0)

    def release(self) -> None:
        self.released = True

    def get(self, _property_id: int) -> float:
        return self.fps

    def isOpened(self) -> bool:
        return self.opened


class RecordingWriter:
    def __init__(self, *, opened: bool = True) -> None:
        self.opened = opened
        self.frames: list[np.ndarray] = []
        self.released = False

    def isOpened(self) -> bool:
        return self.opened

    def write(self, frame: np.ndarray) -> None:
        self.frames.append(frame)

    def release(self) -> None:
        self.released = True


class RecordingCV:
    FONT_HERSHEY_SIMPLEX = 0
    CAP_PROP_FPS = 5

    def __init__(
        self,
        capture: RecordingCapture | None = None,
        writer: RecordingWriter | None = None,
        key: int = -1,
    ) -> None:
        self.capture = capture
        self.writer = writer or RecordingWriter()
        self.key = key
        self.operations: list[str] = []
        self.writer_args: tuple[object, ...] | None = None

    def VideoCapture(self, _source: object) -> RecordingCapture:
        assert self.capture is not None
        return self.capture

    def VideoWriter(self, *args: object) -> RecordingWriter:
        self.writer_args = args
        return self.writer

    def VideoWriter_fourcc(self, *_characters: str) -> int:
        return 1234

    def putText(self, *_args: object) -> None:
        self.operations.append("text")

    def line(self, *_args: object) -> None:
        self.operations.append("line")

    def circle(self, *_args: object) -> None:
        self.operations.append("circle")

    def imshow(self, *_args: object) -> None:
        self.operations.append("show")

    def waitKey(self, _delay: int) -> int:
        return self.key

    def destroyAllWindows(self) -> None:
        self.operations.append("destroy")


class RecordingDetector:
    def __init__(self, analysis: object) -> None:
        self.analysis = analysis
        self.thresholds: list[float] = []
        self.closed = False

    def analyze(self, _frame: np.ndarray, threshold: float) -> object:
        self.thresholds.append(threshold)
        return self.analysis

    def close(self) -> None:
        self.closed = True


def test_run_stream_renders_detected_pose_and_writes_video(tmp_path: Path) -> None:
    """A normal stream draws all landmarks and releases its writer."""
    from hunchback_detection.posture import PostureStatus
    from hunchback_detection.video_stream import run_stream
    from hunchback_detection.vision import FrameAnalysis, LandmarkPoint

    frame = np.zeros((40, 60, 3), dtype=np.uint8)
    capture = RecordingCapture([frame])
    writer = RecordingWriter()
    cv = RecordingCV(writer=writer)
    detector = RecordingDetector(
        FrameAnalysis(
            detected=True,
            angle=170.0,
            status=PostureStatus.GOOD,
            landmarks={
                "ear": LandmarkPoint(10, 10, 1),
                "shoulder": LandmarkPoint(20, 20, 1),
                "hip": LandmarkPoint(30, 30, 1),
            },
        )
    )

    run_stream(
        capture,
        threshold=150,
        output_path=str(tmp_path / "result.mp4"),
        detector=detector,
        cv_module=cv,
    )

    assert detector.thresholds == [150]
    assert cv.operations.count("line") == 2
    assert cv.operations.count("circle") == 3
    assert len(writer.frames) == 1
    assert capture.released and writer.released and detector.closed


def test_run_stream_labels_missing_pose_and_stops_on_q() -> None:
    """The preview explains missing landmarks and honors the quit key."""
    from hunchback_detection.video_stream import run_stream
    from hunchback_detection.vision import FrameAnalysis

    capture = RecordingCapture([np.zeros((4, 4, 3), dtype=np.uint8)] * 2)
    cv = RecordingCV(key=ord("q"))
    detector = RecordingDetector(FrameAnalysis(False, None, None, {}))

    run_stream(capture, detector=detector, cv_module=cv)

    assert detector.thresholds == [160]
    assert "text" in cv.operations
    assert capture.released and detector.closed


def test_run_stream_rejects_unwritable_video_target(tmp_path: Path) -> None:
    """Output validation fails before a writer silently drops frames."""
    from hunchback_detection.video_stream import run_stream
    from hunchback_detection.vision import FrameAnalysis

    capture = RecordingCapture([np.zeros((4, 4, 3), dtype=np.uint8)])
    detector = RecordingDetector(FrameAnalysis(False, None, None, {}))

    with pytest.raises(FileNotFoundError, match="output directory"):
        run_stream(
            capture,
            output_path=str(tmp_path / "missing" / "result.mp4"),
            detector=detector,
            cv_module=RecordingCV(),
        )

    assert capture.released and detector.closed


def test_run_stream_rejects_writer_that_cannot_open(tmp_path: Path) -> None:
    """A failed OpenCV writer is released and reported."""
    from hunchback_detection.video_stream import run_stream
    from hunchback_detection.vision import FrameAnalysis

    capture = RecordingCapture([np.zeros((4, 4, 3), dtype=np.uint8)], fps=float("nan"))
    writer = RecordingWriter(opened=False)
    detector = RecordingDetector(FrameAnalysis(False, None, None, {}))

    with pytest.raises(RuntimeError, match="could not create output video"):
        run_stream(
            capture,
            output_path=str(tmp_path / "result.mp4"),
            detector=detector,
            cv_module=RecordingCV(writer=writer),
        )

    assert writer.released is True


def test_run_live_rejects_unavailable_webcam(monkeypatch: pytest.MonkeyPatch) -> None:
    """Camera-open failures release the native capture immediately."""
    import hunchback_detection.video_stream as video_stream

    capture = RecordingCapture(opened=False)
    monkeypatch.setattr(video_stream, "_load_cv2", lambda: RecordingCV(capture))

    with pytest.raises(RuntimeError, match="default webcam"):
        video_stream.run_live()

    assert capture.released is True


def test_run_video_opens_existing_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid input is forwarded to the shared stream runner."""
    import hunchback_detection.video_stream as video_stream

    source = tmp_path / "source.mp4"
    source.touch()
    capture = RecordingCapture(opened=True)
    cv = RecordingCV(capture)
    received: list[tuple[object, float, str | None]] = []
    monkeypatch.setattr(video_stream, "_load_cv2", lambda: cv)
    monkeypatch.setattr(
        video_stream,
        "run_stream",
        lambda cap, *, threshold, output_path, cv_module: received.append(
            (cap, threshold, output_path)
        ),
    )

    video_stream.run_video(str(source), threshold=145, output_path="out.mp4")

    assert received == [(capture, 145, "out.mp4")]


@pytest.mark.parametrize(
    ("entrypoint", "arguments", "target", "expected"),
    [
        (
            "run_live_cli",
            ["--threshold", "150", "--output-path", "x.mp4"],
            "run_live",
            (150.0, "x.mp4"),
        ),
        (
            "run_video_cli",
            ["--input-path", "in.mp4", "--threshold", "155"],
            "run_video",
            ("in.mp4", 155.0, None),
        ),
    ],
)
def test_cli_entrypoints_forward_arguments(
    entrypoint: str,
    arguments: list[str],
    target: str,
    expected: tuple[object, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Console commands preserve validated user arguments."""
    import hunchback_detection.video_stream as video_stream

    received: list[tuple[object, ...]] = []

    def record_live(*, threshold: float, output_path: str | None) -> None:
        received.append((threshold, output_path))

    def record_video(
        input_path: str, *, threshold: float, output_path: str | None
    ) -> None:
        received.append((input_path, threshold, output_path))

    monkeypatch.setattr(
        video_stream,
        target,
        record_live if target == "run_live" else record_video,
    )
    monkeypatch.setattr(sys, "argv", [entrypoint, *arguments])

    getattr(video_stream, entrypoint)()

    assert received == [expected]
