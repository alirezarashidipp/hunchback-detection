"""Top-level package for hunchback detection.

This package provides functions for computing the posture angle between
an ear, shoulder and hip and classifying the result as good or bad.  It
also exposes convenience functions to run real-time detection on a
webcam or video file.
"""

# Re-export key functions and classes for convenient access.  The
# runtime components (run_live and run_video) are not imported here to
# avoid pulling heavy dependencies like Mediapipe at import time.  To use
# the video streaming utilities, import them directly from
# ``hunchback_detection.video_stream``.
from .posture import PostureResult, calculate_angle, classify_posture  # noqa: F401