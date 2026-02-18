"""Unit tests for hunchback_detection.posture.

These tests validate that the angle calculation and classification
functions behave as expected.  Run them with ``pytest``.
"""

import math

import pytest

from hunchback_detection.posture import calculate_angle, classify_posture


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