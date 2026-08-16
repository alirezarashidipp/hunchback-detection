"""Unit tests for hunchback_detection.posture.

These tests validate that the angle calculation and classification
functions behave as expected.  Run them with ``pytest``.
"""

import math

import pytest

import hunchback_detection.posture as posture
from hunchback_detection.posture import (
    analyze_points,
    calculate_angle,
    classify_posture,
)


def test_calculate_angle_right_angle() -> None:
    """The angle between (1,0)-(0,0)-(0,1) should be 90 degrees."""
    angle = calculate_angle((1, 0), (0, 0), (0, 1))
    assert math.isclose(angle, 90.0, abs_tol=1e-1)


def test_calculate_angle_straight_line() -> None:
    """Three collinear points on a straight line should yield 180 degrees."""
    angle = calculate_angle((-1, 0), (0, 0), (1, 0))
    assert math.isclose(angle, 180.0, abs_tol=1e-1)


def test_calculate_angle_obtuse() -> None:
    """An obtuse angle should be computed correctly."""
    angle = calculate_angle((0, 0), (1, 0), (2, 1))
    # The angle between vectors (-1, 0) and (1, 1) is 135 degrees
    expected = 135.0
    assert math.isclose(angle, expected, abs_tol=1e-1)


def test_classify_posture_good_bad() -> None:
    """Verify that classification follows the threshold."""
    assert classify_posture(170.0, 160.0) == "good"
    assert classify_posture(150.0, 160.0) == "bad"


@pytest.mark.parametrize("value", [59.9, 180.1, float("nan"), float("inf")])
def test_validate_threshold_rejects_values_outside_safe_range(value: float) -> None:
    """Unsafe or non-finite thresholds cannot enter the analysis pipeline."""
    with pytest.raises(ValueError, match="between 60 and 180"):
        posture.validate_threshold(value)


@pytest.mark.parametrize("value", [60.0, 120.5, 180.0])
def test_validate_threshold_accepts_safe_boundaries(value: float) -> None:
    """The documented inclusive threshold range remains usable."""
    assert posture.validate_threshold(value) == value


def test_calculate_angle_rejects_zero_length_vector() -> None:
    """Coincident points must not be silently classified as good posture."""
    with pytest.raises(ValueError, match="distinct"):
        calculate_angle((0, 0), (0, 0), (1, 1))


@pytest.mark.parametrize("point", [(1,), (1, 2, 3), (1, float("nan"))])
def test_calculate_angle_rejects_invalid_points(point: tuple[float, ...]) -> None:
    """Only finite two-dimensional points have a defined screen angle."""
    with pytest.raises(ValueError, match="finite 2D point"):
        calculate_angle(point, (0, 0), (1, 1))


def test_analyze_points_returns_typed_result() -> None:
    """Combined analysis exposes the measured angle and stable status value."""
    result = analyze_points((-1, 0), (0, 0), (1, 0), threshold=160)

    assert result.angle == 180.0
    assert result.status is posture.PostureStatus.GOOD
