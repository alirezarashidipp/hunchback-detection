#!/usr/bin/env python3
"""CLI wrapper to run live hunchback posture detection.

This script delegates to the ``hunchback_detection.video_stream``
module.  Keeping a separate script allows users to call the program
directly without having to know the package internals.  It is also
useful for packaging and installation via ``pip``.
"""

from hunchback_detection.video_stream import run_live_cli


def main() -> None:
    run_live_cli()


if __name__ == "__main__":
    main()
