"""OpenCV webcam and video-file commands using the shared pose analyzer."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

from .posture import PostureStatus, validate_threshold
from .vision import FrameAnalysis, PoseDetector


class Capture(Protocol):
    def read(self) -> tuple[bool, NDArray[np.uint8]]: ...

    def release(self) -> None: ...

    def get(self, property_id: int) -> float: ...


class Detector(Protocol):
    def analyze(
        self,
        frame: NDArray[np.uint8],
        threshold: float,
    ) -> FrameAnalysis: ...

    def close(self) -> None: ...


def _load_cv2() -> Any:
    """Import OpenCV only when a video command actually runs."""
    import cv2

    return cv2


def _draw_analysis(image: NDArray[np.uint8], analysis: FrameAnalysis, cv: Any) -> None:
    """Draw one analysis result onto a copy of the source frame."""
    if not analysis.detected:
        cv.putText(
            image,
            "No side profile detected",
            (16, 36),
            cv.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        return

    ear = analysis.landmarks["ear"]
    shoulder = analysis.landmarks["shoulder"]
    hip = analysis.landmarks["hip"]
    points = [
        (int(ear.x), int(ear.y)),
        (int(shoulder.x), int(shoulder.y)),
        (int(hip.x), int(hip.y)),
    ]
    cv.line(image, points[0], points[1], (255, 170, 35), 2)
    cv.line(image, points[1], points[2], (255, 170, 35), 2)
    for point in points:
        cv.circle(image, point, 4, (245, 245, 245), -1)

    status_is_good = analysis.status is PostureStatus.GOOD
    status_label = "On target" if status_is_good else "Needs attention"
    status_color = (70, 185, 105) if status_is_good else (70, 90, 225)
    cv.putText(
        image,
        f"Shoulder angle: {analysis.angle:.1f}",
        (16, 36),
        cv.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    cv.putText(
        image,
        status_label,
        (16, 70),
        cv.FONT_HERSHEY_SIMPLEX,
        0.7,
        status_color,
        2,
    )


def _create_writer(
    output_path: str,
    frame: NDArray[np.uint8],
    capture: Capture,
    cv: Any,
) -> Any:
    output = Path(output_path).expanduser()
    if not output.parent.exists():
        raise FileNotFoundError(f"output directory does not exist: {output.parent}")

    fps = float(capture.get(cv.CAP_PROP_FPS))
    if not math.isfinite(fps) or fps <= 0:
        fps = 20.0
    height, width = frame.shape[:2]
    writer = cv.VideoWriter(
        str(output),
        cv.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if hasattr(writer, "isOpened") and not writer.isOpened():
        writer.release()
        raise RuntimeError(f"could not create output video: {output}")
    return writer


def run_stream(
    cap: Capture,
    *,
    threshold: float = 160.0,
    output_path: str | None = None,
    detector: Detector | None = None,
    cv_module: Any | None = None,
) -> None:
    """Analyze an open capture until it ends or the user presses Q/Escape."""
    safe_threshold = validate_threshold(threshold)
    cv = cv_module or _load_cv2()
    active_detector = detector or PoseDetector()
    writer = None

    try:
        while True:
            received, frame = cap.read()
            if not received:
                break

            analysis = active_detector.analyze(frame, safe_threshold)
            rendered = frame.copy()
            _draw_analysis(rendered, analysis, cv)

            if output_path and writer is None:
                writer = _create_writer(output_path, rendered, cap, cv)
            if writer is not None:
                writer.write(rendered)

            cv.imshow("Posture Coach", rendered)
            key = cv.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        active_detector.close()
        cv.destroyAllWindows()


def run_live(threshold: float = 160.0, output_path: str | None = None) -> None:
    """Analyze the default host webcam in an OpenCV window."""
    cv = _load_cv2()
    capture = cv.VideoCapture(0)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError("could not open the default webcam")
    run_stream(
        capture,
        threshold=threshold,
        output_path=output_path,
        cv_module=cv,
    )


def run_video(
    input_path: str,
    *,
    threshold: float = 160.0,
    output_path: str | None = None,
) -> None:
    """Analyze one existing video file in an OpenCV window."""
    source = Path(input_path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"input video does not exist: {source}")

    cv = _load_cv2()
    capture = cv.VideoCapture(str(source))
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"could not open video file: {source}")
    run_stream(
        capture,
        threshold=threshold,
        output_path=output_path,
        cv_module=cv,
    )


def run_live_cli() -> None:
    """Parse webcam command arguments and start live analysis."""
    parser = argparse.ArgumentParser(
        description="Run local posture feedback with the default webcam."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=160.0,
        help="good-posture threshold in degrees (60–180; default: 160)",
    )
    parser.add_argument("--output-path", help="optional annotated MP4 output path")
    args = parser.parse_args()
    run_live(threshold=args.threshold, output_path=args.output_path)


def run_video_cli() -> None:
    """Parse video command arguments and start file analysis."""
    parser = argparse.ArgumentParser(description="Analyze an existing posture video.")
    parser.add_argument("--input-path", required=True, help="input video path")
    parser.add_argument(
        "--threshold",
        type=float,
        default=160.0,
        help="good-posture threshold in degrees (60–180; default: 160)",
    )
    parser.add_argument("--output-path", help="optional annotated MP4 output path")
    args = parser.parse_args()
    run_video(
        args.input_path,
        threshold=args.threshold,
        output_path=args.output_path,
    )
