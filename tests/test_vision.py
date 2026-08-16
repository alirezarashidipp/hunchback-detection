"""Tests for the MediaPipe boundary and frame analysis."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pytest


@dataclass
class FakeLandmark:
    x: float = 0.0
    y: float = 0.0
    visibility: float = 1.0


class FakePoseModel:
    def __init__(self, landmarks: list[FakeLandmark] | None) -> None:
        pose_landmarks = None
        if landmarks is not None:
            pose_landmarks = SimpleNamespace(landmark=landmarks)
        self.result = SimpleNamespace(pose_landmarks=pose_landmarks)
        self.received_frame: np.ndarray | None = None
        self.closed = False

    def process(self, frame: np.ndarray) -> SimpleNamespace:
        self.received_frame = frame
        return self.result

    def close(self) -> None:
        self.closed = True


def make_frame(width: int = 200, height: int = 100) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[0, 0] = [10, 20, 30]
    return frame


def make_landmarks(*, visibility: float = 1.0) -> list[FakeLandmark]:
    landmarks = [FakeLandmark() for _ in range(24)]
    landmarks[7] = FakeLandmark(0.25, 0.2, visibility)
    landmarks[11] = FakeLandmark(0.5, 0.5, visibility)
    landmarks[23] = FakeLandmark(0.75, 0.8, visibility)
    return landmarks


def test_analyze_returns_no_pose_when_landmarks_are_absent() -> None:
    from hunchback_detection.vision import PoseDetector

    detector = PoseDetector(pose_model=FakePoseModel(None))

    result = detector.analyze(make_frame(), threshold=150)

    assert result.detected is False
    assert result.angle is None
    assert result.status is None
    assert result.landmarks == {}


def test_analyze_maps_visible_left_landmarks_to_pixels() -> None:
    from hunchback_detection.posture import PostureStatus
    from hunchback_detection.vision import PoseDetector

    pose_model = FakePoseModel(make_landmarks())
    detector = PoseDetector(pose_model=pose_model)

    result = detector.analyze(make_frame(), threshold=150)

    assert result.detected is True
    assert result.status is PostureStatus.GOOD
    assert result.landmarks["ear"].x == 50.0
    assert result.landmarks["shoulder"].y == 50.0
    assert result.landmarks["hip"].x == 150.0
    assert pose_model.received_frame is not None
    assert pose_model.received_frame[0, 0].tolist() == [30, 20, 10]


def test_analyze_treats_low_visibility_as_no_pose() -> None:
    from hunchback_detection.vision import PoseDetector

    detector = PoseDetector(
        pose_model=FakePoseModel(make_landmarks(visibility=0.2)),
        minimum_visibility=0.5,
    )

    assert detector.analyze(make_frame(), threshold=150).detected is False


def test_analyze_rejects_empty_frame() -> None:
    from hunchback_detection.vision import PoseDetector

    detector = PoseDetector(pose_model=FakePoseModel(None))

    with pytest.raises(ValueError, match="non-empty BGR"):
        detector.analyze(np.array([]), threshold=150)


def test_detector_closes_owned_pose_model() -> None:
    from hunchback_detection.vision import PoseDetector

    pose_model = FakePoseModel(None)

    with PoseDetector(pose_model=pose_model):
        pass

    assert pose_model.closed is True
