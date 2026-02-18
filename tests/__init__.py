"""Configure test environment for hunchback_detection.

This module modifies ``sys.path`` so that the package under ``src`` is
importable when running tests without installation.  It appends the
project's ``src`` directory to ``sys.path`` if it is not already
present.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)