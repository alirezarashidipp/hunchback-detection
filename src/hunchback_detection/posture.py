"""Framework-independent posture geometry and classification."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

Number = float | int
Point = tuple[Number, Number]

MIN_THRESHOLD = 60.0
MAX_THRESHOLD = 180.0


class PostureStatus(str, Enum):
    """Stable machine-readable posture classifications."""

    GOOD = "good"
    BAD = "bad"


@dataclass(frozen=True, slots=True)
class PostureResult:
    """The angle measured at the shoulder and its classification."""

    angle: float
    status: PostureStatus


def validate_threshold(value: float) -> float:
    """Return a safe posture threshold or raise a clear validation error."""
    threshold = float(value)
    if not math.isfinite(threshold) or not MIN_THRESHOLD <= threshold <= MAX_THRESHOLD:
        raise ValueError("threshold must be between 60 and 180 degrees")
    return threshold


def _as_point(value: Sequence[Number], name: str) -> NDArray[np.float64]:
    """Convert a public point value to a finite two-dimensional array."""
    point = np.asarray(value, dtype=float)
    if point.shape != (2,) or not np.isfinite(point).all():
        raise ValueError(f"{name} must be a finite 2D point")
    return point


def calculate_angle(
    p1: Sequence[Number],
    p2: Sequence[Number],
    p3: Sequence[Number],
) -> float:
    """Calculate the smaller angle at ``p2`` in degrees.

    Coincident points are rejected because they do not define an angle and
    must never be interpreted as good posture.
    """
    first = _as_point(p1, "p1")
    vertex = _as_point(p2, "p2")
    third = _as_point(p3, "p3")

    vector_a = first - vertex
    vector_b = third - vertex
    norm_a = float(np.linalg.norm(vector_a))
    norm_b = float(np.linalg.norm(vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("angle points must be distinct from the vertex")

    cosine = float(np.dot(vector_a, vector_b) / (norm_a * norm_b))
    bounded_cosine = max(-1.0, min(1.0, cosine))
    return math.degrees(math.acos(bounded_cosine))


def classify_posture(
    angle: float,
    threshold: float = 160.0,
) -> PostureStatus:
    """Classify an angle using an inclusive validated threshold."""
    measured_angle = float(angle)
    if not math.isfinite(measured_angle) or not 0.0 <= measured_angle <= 180.0:
        raise ValueError("angle must be between 0 and 180 degrees")

    safe_threshold = validate_threshold(threshold)
    if measured_angle >= safe_threshold:
        return PostureStatus.GOOD
    return PostureStatus.BAD


def analyze_points(
    p1: Sequence[Number],
    p2: Sequence[Number],
    p3: Sequence[Number],
    *,
    threshold: float = 160.0,
) -> PostureResult:
    """Measure and classify one ear-shoulder-hip point set."""
    angle = calculate_angle(p1, p2, p3)
    status = classify_posture(angle, threshold)
    return PostureResult(angle=angle, status=status)
