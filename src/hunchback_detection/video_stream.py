"""Video streaming utilities for hunchback detection.

This module contains functions to run posture detection on either a
webcam feed or a video file.  The core functionality is provided by
``run_stream``, which takes an ``cv2.VideoCapture`` object and
processes each frame.  Convenience functions wrap this to open
appropriate inputs.

When executed via the CLI entry points (see ``pyproject.toml``),
the ``run_live_cli`` and ``run_video_cli`` functions parse command-line
arguments and call the underlying functions.
"""

from __future__ import annotations

import argparse
import cv2
import mediapipe as mp
from typing import Optional

from .posture import calculate_angle, classify_posture


def run_stream(
    cap: cv2.VideoCapture,
    *,
    threshold: float = 160.0,
    output_path: Optional[str] = None,
) -> None:
    """Process frames from an open ``cv2.VideoCapture`` object.

    This function reads frames one-by-one from ``cap``, runs
    MediaPipe's pose estimator to locate the ear, shoulder and hip
    landmarks, computes the posture angle and classification, and
    overlays the results on the frame.  Optionally, it writes the
    annotated output to a video file.  Press ``Esc`` or ``q`` in the
    window to terminate early.

    Args:
        cap: An open ``cv2.VideoCapture`` providing frames to process.
        threshold: Angle threshold for classifying posture.  Larger
            values require a more upright posture to be classified as
            good.
        output_path: Optional path to write an annotated video.  If
            provided, a ``cv2.VideoWriter`` will be created on the first
            frame and all subsequent frames will be written to that file.

    Returns:
        None
    """
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    mp_drawing = mp.solutions.drawing_utils
    writer = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Convert the BGR image to RGB before processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        # Convert back to BGR for OpenCV rendering
        image = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            height, width, _ = image.shape
            landmarks = results.pose_landmarks.landmark
            try:
                # Extract the left ear, shoulder and hip landmarks
                ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
                shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                p1 = (ear.x * width, ear.y * height)
                p2 = (shoulder.x * width, shoulder.y * height)
                p3 = (hip.x * width, hip.y * height)
                angle = calculate_angle(p1, p2, p3)
                status = classify_posture(angle, threshold)
                # Draw lines connecting the points
                cv2.line(
                    image,
                    (int(p1[0]), int(p1[1])),
                    (int(p2[0]), int(p2[1])),
                    (0, 255, 0),
                    2,
                )
                cv2.line(
                    image,
                    (int(p2[0]), int(p2[1])),
                    (int(p3[0]), int(p3[1])),
                    (0, 255, 0),
                    2,
                )
                # Draw points
                for p in (p1, p2, p3):
                    cv2.circle(image, (int(p[0]), int(p[1])), 4, (0, 0, 255), -1)
                # Display angle and status
                cv2.putText(
                    image,
                    f"Angle: {angle:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    image,
                    f"Posture: {status}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255) if status == "bad" else (0, 255, 0),
                    2,
                )
            except IndexError:
                # Some landmarks may be missing if the person is not fully
                # visible; skip drawing in that case
                pass

            # Draw full pose connections for context
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
            )

        # Write to output file if requested
        if output_path:
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
                writer = cv2.VideoWriter(
                    output_path,
                    fourcc,
                    fps,
                    (image.shape[1], image.shape[0]),
                )
            writer.write(image)
        # Display the image to the user
        cv2.imshow("Hunchback Detection", image)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()


def run_live(threshold: float = 160.0, output_path: Optional[str] = None) -> None:
    """Run posture detection on the default webcam.

    Args:
        threshold: Angle threshold for classification.
        output_path: Optional path to write annotated output.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam.")
    run_stream(cap, threshold=threshold, output_path=output_path)


def run_video(
    input_path: str, *, threshold: float = 160.0, output_path: Optional[str] = None
) -> None:
    """Run posture detection on a video file.

    Args:
        input_path: Path to the input video file.
        threshold: Angle threshold for classification.
        output_path: Optional path to write annotated output.
    """
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {input_path}")
    run_stream(cap, threshold=threshold, output_path=output_path)


def run_live_cli() -> None:
    """Entry point for the ``hunchback-live`` console script.

    This function parses command-line arguments and calls
    :func:`run_live`.
    """
    parser = argparse.ArgumentParser(
        description="Run real-time hunchback posture detection on webcam."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=160.0,
        help="Angle threshold in degrees for classifying posture (default: 160)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Optional path to save the annotated video (MP4 format)",
    )
    args = parser.parse_args()
    run_live(threshold=args.threshold, output_path=args.output_path)


def run_video_cli() -> None:
    """Entry point for the ``hunchback-video`` console script.

    This function parses command-line arguments and calls
    :func:`run_video`.
    """
    parser = argparse.ArgumentParser(
        description="Run hunchback posture detection on a video file."
    )
    parser.add_argument(
        "--input-path",
        type=str,
        required=True,
        help="Path to the input video file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=160.0,
        help="Angle threshold in degrees for classifying posture (default: 160)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Optional path to save the annotated video (MP4 format)",
    )
    args = parser.parse_args()
    run_video(
        input_path=args.input_path,
        threshold=args.threshold,
        output_path=args.output_path,
    )