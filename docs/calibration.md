# Calibration guide

Calibration personalizes the feedback threshold to the current person, chair,
camera height, and camera angle. It is an ergonomic baseline, not a medical
measurement.

## Before starting

1. Place the camera roughly level with your upper body.
2. Turn sideways enough that the left ear, shoulder, and hip remain visible.
3. Use even lighting and avoid loose clothing that hides the shoulder line.
4. Sit in a comfortable upright position you can reproduce.

## Algorithm

The browser collects 30 valid angle readings. Invalid or missing-pose results do
not advance progress. It uses the median as the upright baseline, subtracts a
12-degree tolerance, and clamps the resulting threshold to 60–180 degrees.

An angle at or above the personal threshold is labeled `good`; a lower angle is
labeled `bad`. Session timing uses the previous valid state and caps any single
update interval at two seconds so a paused tab cannot create a large false
duration.

## Session statistics

- **Shoulder angle:** latest valid ear–shoulder–hip angle.
- **Personal threshold:** calibrated boundary for the current page.
- **Upright:** share of measured session time labeled `good`.
- **Needs attention:** measured time labeled `bad`.

The statistics reset on page refresh, page close, or a new session. Select
**Recalibrate** after moving the camera, changing seats, or substantially
changing your position.

## Interpreting feedback

Use the signal as a gentle reminder to vary position and adjust your workspace.
Pose estimation can be wrong because of occlusion, lighting, clothing, body
variation, or perspective. Persistent pain or health concerns require advice
from a qualified professional rather than this application.
