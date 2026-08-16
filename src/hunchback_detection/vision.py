"""MediaPipe adapter for deterministic posture frame analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

from .posture import PostureStatus, analyze_points, validate_threshold

LEFT_EAR_INDEX = 7
LEFT_SHOULDER_INDEX = 11
LEFT_HIP_INDEX = 23


class PoseModel(Protocol):
    """The small MediaPipe model surface used by the analyzer."""

    def process(self, frame: NDArray[np.uint8]) -> Any: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class LandmarkPoint:
    """A detected landmark expressed in frame pixels."""

    x: float
    y: float
    visibility: float


@dataclass(frozen=True, slots=True)
class FrameAnalysis:
    """One frame's posture result without retaining the source image."""

    detected: bool
    angle: float | None
    status: PostureStatus | None
    landmarks: dict[str, LandmarkPoint]


def _create_pose_model() -> PoseModel:
    """Create the production MediaPipe model only when it is needed."""
    import mediapipe as mp

    return mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )


class PoseDetector:
    """Convert BGR frames into validated posture measurements."""

    def __init__(
        self,
        pose_model: PoseModel | None = None,
        *,
        minimum_visibility: float = 0.5,
    ) -> None:
        if not 0.0 <= minimum_visibility <= 1.0:
            raise ValueError("minimum_visibility must be between 0 and 1")
        self._pose_model = pose_model or _create_pose_model()
        self._minimum_visibility = minimum_visibility
        self._closed = False

    def analyze(
        self,
        frame: NDArray[np.uint8],
        threshold: float = 160.0,
    ) -> FrameAnalysis:
        """Analyze one non-empty BGR image without retaining it."""
        if frame.ndim != 3 or frame.shape[2] != 3 or frame.size == 0:
            raise ValueError("frame must be a non-empty BGR image")
        if self._closed:
            raise RuntimeError("pose detector is closed")

        safe_threshold = validate_threshold(threshold)
        rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])
        result = self._pose_model.process(rgb_frame)
        if result.pose_landmarks is None:
            return self._no_pose()

        raw_landmarks = result.pose_landmarks.landmark
        required = {
            "ear": raw_landmarks[LEFT_EAR_INDEX],
            "shoulder": raw_landmarks[LEFT_SHOULDER_INDEX],
            "hip": raw_landmarks[LEFT_HIP_INDEX],
        }
        if any(
            landmark.visibility < self._minimum_visibility
            for landmark in required.values()
        ):
            return self._no_pose()

        height, width = frame.shape[:2]
        landmarks = {
            name: LandmarkPoint(
                x=float(landmark.x * width),
                y=float(landmark.y * height),
                visibility=float(landmark.visibility),
            )
            for name, landmark in required.items()
        }
        posture = analyze_points(
            (landmarks["ear"].x, landmarks["ear"].y),
            (landmarks["shoulder"].x, landmarks["shoulder"].y),
            (landmarks["hip"].x, landmarks["hip"].y),
            threshold=safe_threshold,
        )
        return FrameAnalysis(
            detected=True,
            angle=posture.angle,
            status=posture.status,
            landmarks=landmarks,
        )

    def close(self) -> None:
        """Release native MediaPipe resources once."""
        if self._closed:
            return
        self._pose_model.close()
        self._closed = True

    def __enter__(self) -> PoseDetector:
        return self

    def __exit__(self, *_error: object) -> None:
        self.close()

    @staticmethod
    def _no_pose() -> FrameAnalysis:
        return FrameAnalysis(
            detected=False,
            angle=None,
            status=None,
            landmarks={},
        )
