# Professional Posture Detection Web App Design

## Goal

Turn the existing posture-detection package into a portfolio-quality, local-first product with a polished browser experience, a maintained Python API and CLI, reproducible Docker setup, strong automated checks, and complete English documentation.

The primary success criterion is that a new user can clone the repository, run one Docker command, open a local URL, grant camera access, calibrate their posture, and receive useful live feedback without any image or session data being persisted.

## Product Scope

The first release will provide:

- A responsive browser application centered on live webcam posture feedback.
- Personal calibration that establishes a session-specific baseline.
- Live posture angle, status color, poor-posture duration, good-posture percentage, and session duration.
- Clear camera, calibration, detection, and connection states.
- A reusable Python posture-analysis API.
- Maintained CLI commands for webcam and video-file processing.
- A single-container local Docker workflow.
- English-only project and contributor documentation.

The first release will not provide user accounts, a database, cloud deployment automation, medical diagnosis, long-term history, alerts outside the browser, or multi-person analysis.

## Architecture

The application uses one Python service and a dependency-free modular frontend:

1. FastAPI serves the web page and static frontend assets.
2. Browser JavaScript requests webcam permission and renders the local video preview.
3. The browser samples resized JPEG frames at a controlled rate and sends them through one WebSocket connection.
4. The backend decodes each frame in memory and uses MediaPipe to extract pose landmarks.
5. A shared analysis module calculates the ear-shoulder-hip angle and produces a structured result.
6. The backend returns small JSON messages containing measurements and detection state, never image data.
7. The browser computes and displays ephemeral calibration and session statistics.

This structure keeps deployment simple, avoids a Node.js build pipeline, and lets the web app and CLI reuse the same Python analysis logic.

## Components and Boundaries

### Core domain module

The core module owns point validation, angle calculation, threshold validation, posture classification, and typed result models. It has no dependency on FastAPI, OpenCV windows, browser state, or file storage.

### Pose detector

The detector owns MediaPipe lifecycle and converts an image into normalized landmarks or a clear no-pose result. It does not classify session statistics or render UI.

### Frame analyzer

The analyzer converts a decoded frame into a JSON-safe result containing the posture angle, posture status, confidence/detection state, and landmark coordinates required for the browser overlay. It uses the core domain module for classification.

### Web application

FastAPI owns HTTP routes, static assets, health checks, WebSocket connection lifecycle, message validation, and safe error responses. It does not persist frames or results.

### Browser application

The frontend is split into small JavaScript modules for camera capture, WebSocket transport, calibration/session state, overlay drawing, and DOM rendering. Browser memory is the only location used for calibration and session metrics.

### CLI

The webcam and video commands continue to use OpenCV windows and the shared detector/analyzer. Existing command names remain available, with validated options and actionable errors.

## Live Data Flow

1. The user opens the local page and explicitly starts the camera.
2. The browser obtains a video stream and opens the analysis WebSocket.
3. During calibration, the frontend collects a bounded set of valid angle samples and derives a robust baseline from their median.
4. The frontend calculates a personalized threshold from the baseline using a documented, bounded offset.
5. The browser sends a resized frame plus the current threshold only when the previous frame is no longer in flight, preventing an unbounded queue.
6. The backend validates the message size and threshold, analyzes the frame, and returns one result.
7. The frontend updates the overlay and accumulates session time only while valid pose results are arriving.
8. Stopping the camera, refreshing, or closing the tab discards all captured and derived data.

## User Experience

The page will have a restrained, professional visual system rather than a generic dashboard. The camera view is the primary element. A compact status panel displays current posture, angle, connection state, and calibration progress. Session metrics appear below the live view and remain readable on mobile and desktop.

The UI distinguishes these states explicitly: idle, requesting permission, connecting, calibrating, tracking good posture, tracking posture that needs attention, no person detected, disconnected, and error. Copy avoids diagnostic medical claims. The repository retains its existing name, while user-facing language describes posture feedback and includes a clear wellness-not-medical-advice notice.

## Privacy and Security

- No frame, video, landmark, calibration value, or session statistic is written to disk or a database.
- The service binds to a documented local address by default.
- WebSocket payloads have a strict maximum size and validated message structure.
- Only expected image formats and bounded numeric thresholds are accepted.
- Error responses do not expose stack traces to the browser.
- Container execution uses a non-root user and a minimal runtime configuration where supported by MediaPipe.
- The privacy behavior and browser camera permissions are documented prominently.

## Error Handling

Camera denial, missing camera hardware, unsupported browser APIs, lost WebSocket connections, invalid payloads, oversized frames, decode failures, missing pose landmarks, MediaPipe failures, invalid CLI paths, and unwritable output paths each receive a specific user-facing or CLI error.

Transient no-pose frames do not fail the session. The UI retains the connection, pauses statistics, and tells the user how to return to view. Backend resources are released on disconnect and CLI video resources are released through deterministic cleanup.

## Testing and Quality Gates

The test suite will include:

- Unit tests for geometry, validation, classification, calibration, and session-statistics rules.
- Unit tests for frame-analysis behavior using fakes at the MediaPipe boundary.
- FastAPI tests for the page, health endpoint, static files, WebSocket validation, and representative success/error messages.
- CLI parser and failure-path tests that do not require a physical camera.
- Frontend logic tests where practical without introducing a large JavaScript framework.
- Container build and health-check verification.

Automated quality gates will run formatting, linting, type checking, tests with coverage, package build validation, and a lightweight security/dependency check. GitHub Actions will run supported Python versions and a Docker build. Tests requiring a real webcam remain documented manual checks because CI runners do not provide camera hardware.

## Packaging and Docker

`pyproject.toml` becomes the single source of package metadata and dependencies, with optional development dependencies. The source layout and existing console entry points remain. Generated bytecode and local environments are removed from version control and covered by `.gitignore`.

The Docker setup includes a production-oriented `Dockerfile`, `.dockerignore`, health check, non-root execution, and `compose.yaml` for a one-command local start. The browser supplies the camera, so the container does not require direct access to a host webcam device.

## Documentation Set

The repository will include:

- `README.md`: product overview, screenshot/demo area, quick start, Docker and native setup, usage, architecture summary, privacy notice, limitations, and project status.
- `AGENTS.md`: repository map, coding conventions, commands, safety constraints, and verification expectations for coding agents.
- `CONTRIBUTING.md`: development setup, workflow, tests, commits, and pull requests.
- `CODE_OF_CONDUCT.md`: contributor behavior expectations.
- `SECURITY.md`: responsible reporting and supported-version policy.
- `CHANGELOG.md`: release history in Keep a Changelog style.
- `docs/architecture.md`: component boundaries and live data flow.
- `docs/privacy.md`: precise ephemeral-data guarantees and threat boundaries.
- `docs/calibration.md`: calibration method, interpretation, and limitations.
- `docs/troubleshooting.md`: camera, browser, MediaPipe, Docker, and codec failures.
- `docs/development.md`: local environment and quality commands.

Repository templates and metadata will include issue templates, a pull request template, Dependabot configuration, CI workflows, license metadata, and suitable GitHub topics/instructions in the README.

## Compatibility and Migration

The public geometry and classification functions and current CLI command names remain available. Existing tests become the baseline and are expanded. The accidental README text corruption is corrected as part of the intentional documentation rewrite. No existing user-authored source changes outside that README edit are present at design time.

## Release Completion Criteria

The work is ready to push when:

- All automated checks pass locally.
- The package builds and its metadata validates.
- The Docker image builds and its health endpoint responds.
- The web app is exercised in a real browser; camera-dependent behavior is verified if host camera permission is available, otherwise it is explicitly recorded as the only manual unverified check.
- The repository contains no generated bytecode, secrets, stored captures, or undocumented setup requirements.
- Documentation commands match the verified implementation.
- The final commit history is coherent and the intended branch is pushed to the configured GitHub remote.
