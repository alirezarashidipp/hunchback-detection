# Architecture

Posture Coach has one analysis core and two delivery surfaces: a local web app
and OpenCV-based command-line tools. The web path is the primary product.

## Data flow

```text
Browser                         Local Python process
-------                         --------------------
getUserMedia camera
  -> canvas JPEG (max 640 px)
  -> one in-flight WebSocket frame
                                -> validate JSON and 1 MB image limit
                                -> decode JPEG in memory
                                -> MediaPipe pose landmarks
                                -> ear–shoulder–hip angle
  <- analysis JSON              <- discard frame after request
  -> calibration and metrics
  -> canvas pose overlay
```

The browser targets five frames per second and waits for each response before
sending another frame. This bounds work and prevents a slow analyzer from
building an unbounded queue.

## Python modules

- `posture.py` owns validated geometry and classification. It has no camera,
  web, or MediaPipe dependency.
- `vision.py` adapts MediaPipe landmarks to the posture domain and returns an
  immutable frame result. The model is created lazily and can be replaced by a
  test double.
- `web.py` owns HTTP assets, frame validation, and the WebSocket lifecycle. One
  detector belongs to one connection and is closed on disconnect.
- `video_stream.py` owns OpenCV capture, rendering, and resource cleanup for
  webcam and file commands while reusing the same detector.

## Browser modules

- `camera.js` owns permission, media tracks, and bounded JPEG capture.
- `connection.js` owns WebSocket state and the one-frame-in-flight rule.
- `session.js` owns calibration and ephemeral session calculations.
- `overlay.js` draws landmarks without modifying the source video.
- `app.js` coordinates modules and renders accessible UI state.

## WebSocket contract

The client sends a text JSON message:

```json
{
  "type": "frame",
  "image": "data:image/jpeg;base64,...",
  "threshold": 148.5
}
```

The server returns either an analysis object or a stable error object. An
analysis includes `detected`, nullable `angle` and `status`, plus pixel-space
`ear`, `shoulder`, and `hip` landmarks when detected. Errors contain `type`,
`code`, and a safe message. Raw exception details and image contents are not
returned.

## Design choices

- FastAPI serves static assets and the WebSocket from one process, avoiding a
  cross-origin setup for local users.
- Personal state stays in JavaScript because it is useful only to the current
  page and does not belong in a server-side identity or database.
- MediaPipe is pinned to `0.10.21`; the analyzer intentionally uses its legacy
  `solutions` API. A dependency-contract test protects this boundary.
- The container is local-only by default. Internet deployment requires a
  separate threat model described in `SECURITY.md`.
