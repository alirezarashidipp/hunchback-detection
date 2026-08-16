#!/usr/bin/env python3
"""CLI wrapper to run hunchback posture detection on a video file.

This script delegates to the ``hunchback_detection.video_stream``
module.  Keeping a separate script allows users to call the program
directly without having to know the package internals.
"""

from hunchback_detection.video_stream import run_video_cli


def main() -> None:
    run_video_cli()


if __name__ == "__main__":
    main()
