# Hunchback Detection

This project implements a real‑time posture detection system using MediaPipe and
OpenCV.  It calculates key body angles from a webcam or video stream and
classifies whether the posture is good or indicative of a forward head (i.e.
hunchback) posture.  The original repository consisted of a single script with
no tests, packaging or documentation.  This refactor introduces a modular
Python package, command‑line utilities, a notebook demo and continuous
integration so that you can easily extend and maintain the project.

## Features

* **Real‑time detection** – process live webcam frames or pre‑recorded video
  files using MediaPipe's pose estimation and OpenCV for rendering.
* **Angle calculation** – compute the angle between the ear, shoulder and hip
  landmarks to assess back posture.  Angles close to 180° indicate an upright
  posture while smaller angles correspond to a hunched position.
* **Posture classification** – a configurable threshold classifies the
  measured angle as **good** or **bad**.  The classification and angle are
  overlaid on the video for immediate feedback.
* **Modular API** – reusable functions in `hunchback_detection/posture.py`
  calculate angles and perform classification.  A simple dataclass holds
  posture results.
* **Command‑line scripts** – run the live detection (`scripts/run_live.py`) or
  process a video file (`scripts/run_video.py`) without writing any code.
* **Tests** – unit tests in `tests/test_posture.py` verify angle
  calculations and classification logic.
* **Continuous integration** – a GitHub Actions workflow runs the test suite
  automatically on each push.
* **Packaging** – a `pyproject.toml` provides metadata and exposes
  entry‑points for command‑line usage.

## Installation

You will need Python 3.8 or later.  Create a virtual environment and
install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

MediaPipe depends on additional system libraries; consult the
[MediaPipe installation guide](https://google.github.io/mediapipe/getting_started/install.html)
if you encounter build errors.  On Linux you may need to install `libgl1` or
similar packages for OpenCV.

## Usage

### Live webcam detection

To start real‑time posture detection from your webcam, run:

```bash
python scripts/run_live.py --threshold 160
```

The `threshold` determines the angle (in degrees) below which the posture is
classified as **bad**.  Try values between 150 and 170 to find an
appropriate setting for your environment.

### Video file detection

To analyse an existing video, specify the path to the file:

```bash
python scripts/run_video.py --input-path path/to/video.mp4 --threshold 160
```

The processed video will be displayed frame‑by‑frame with overlays.  To
write the annotated output to disk, pass `--output-path output.mp4`.

### Library usage

The underlying functions can be imported into your own programs:

```python
from hunchback_detection.posture import calculate_angle, classify_posture

# Compute the angle at the origin for three points forming a right angle
angle = calculate_angle((1, 0), (0, 0), (0, 1))
posture = classify_posture(angle, threshold=160)
print(angle, posture)
```

## Project structure

```
hunchback_detection/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── scripts/
│   ├── run_live.py          # Run live webcam posture detection
│   └── run_video.py         # Run posture detection on a video file
├── src/
│   └── hunchback_detection/
│       ├── __init__.py
│       ├── posture.py       # Angle calculation and posture classification
│       └── video_stream.py  # Functions to run detection on webcam/video
├── tests/
│   └── test_posture.py      # Unit tests for the core logic
├── notebooks/
│   └── posture_detection_demo.ipynb  # Example notebook (optional)
└── .github/workflows/python-app.yml  # CI pipeline
```

## Contributing

Contributions are welcome!  Please open an issue to discuss your idea, or
submit a pull request with your improvements.

## License

Distributed under the MIT License.  See `LICENSE` for details.