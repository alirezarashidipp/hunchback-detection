"""Utilities for computing body angles and classifying posture.

This module defines helper functions to compute the angle between three
points and classify the resulting posture as either ``"good"`` or
``"bad"`` based on a configurable threshold.  A dataclass is used to
bundle angle and classification results together.

Example:

    >>> from hunchback_detection.posture import calculate_angle, classify_posture
    >>> angle = calculate_angle((1, 0), (0, 0), (0, 1))
    >>> status = classify_posture(angle, threshold=160)
    >>> print(angle, status)
    90.0 'bad'

These functions are unit-tested in ``tests/test_posture.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Tuple
import math
import numpy as np


Number = float | int
Point = Tuple[Number, Number]  # alias for 2D point


@dataclass
class PostureResult:
    """Container for posture analysis results.

    Attributes:
        angle: The measured angle in degrees at the shoulder, formed by the
            line segments ear–shoulder and shoulder–hip.
        status: A string, either ``"good"`` if the angle is above the
            threshold or ``"bad"`` otherwise.
    """

    angle: float
    status: str


def calculate_angle(p1: Sequence[Number], p2: Sequence[Number], p3: Sequence[Number]) -> float:
    """Compute the angle (in degrees) between three points at ``p2``.

    The function treats the three inputs as vectors in 2D space and
    computes the angle between the vectors ``p1 - p2`` and ``p3 - p2``.  It
    returns the smaller of the two possible angles between the vectors,
    normalized to the range [0, 180].  If any vector has zero length, the
    function returns 180 to indicate a straight line.

    Args:
        p1: Coordinates of the first point.
        p2: Coordinates of the vertex point.
        p3: Coordinates of the third point.

    Returns:
        The angle at ``p2`` in degrees.
    """
    a = np.array(p1, dtype=float) - np.array(p2, dtype=float)
    b = np.array(p3, dtype=float) - np.array(p2, dtype=float)
    # compute norms
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        # If either vector has zero length, we cannot define an angle;
        # treat as straight line (180°) so that posture is considered good.
        return 180.0
    # compute cosine of angle using dot product formula
    cos_theta = float(np.dot(a, b) / (norm_a * norm_b))
    # Numerical errors could push cos_theta slightly outside [-1, 1]
    cos_theta = max(min(cos_theta, 1.0), -1.0)
    angle_rad = math.acos(cos_theta)
    angle_deg = math.degrees(angle_rad)
    return angle_deg


def classify_posture(angle: float, threshold: float = 160.0) -> str:
    """Classify posture quality based on the measured angle.

    Args:
        angle: The angle (in degrees) between ear–shoulder and shoulder–hip.
        threshold: The minimum angle considered a good posture.  Angles
            below this threshold are classified as ``"bad"``.

    Returns:
        ``"good"`` if ``angle >= threshold``, otherwise ``"bad"``.
    """
    return "good" if angle >= threshold else "bad"


def analyze_points(
    p1: Sequence[Number],
    p2: Sequence[Number],
    p3: Sequence[Number],
    *,
    threshold: float = 160.0,
) -> PostureResult:
    """Compute the angle between three points and classify the result.

    This helper calls :func:`calculate_angle` and :func:`classify_posture`
    and returns a :class:`PostureResult` with both the angle and the
    classification.

    Args:
        p1: First point.
        p2: Vertex point.
        p3: Third point.
        threshold: Classification threshold.

    Returns:
        A :class:`PostureResult` containing the angle and classification.
    """
    angle = calculate_angle(p1, p2, p3)
    status = classify_posture(angle, threshold)
    return PostureResult(angle=angle, status=status)