# Professional Posture Detection Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a portfolio-quality, local-first posture detection product with a live browser camera, personal calibration, ephemeral session metrics, maintained CLI, Docker workflow, automated quality gates, and complete English documentation.

**Architecture:** FastAPI serves a dependency-free modular HTML/CSS/JavaScript frontend and accepts resized JPEG frames over a bounded WebSocket protocol. A MediaPipe adapter analyzes frames in memory and delegates geometry and classification to a framework-independent Python core shared with the CLI.

**Tech Stack:** Python 3.11-3.12, FastAPI, Uvicorn, MediaPipe, OpenCV headless for web/container use, NumPy, HTML5 MediaDevices/Canvas, CSS, JavaScript ES modules, Pytest, Ruff, MyPy, Coverage, Docker, GitHub Actions.

## Global Constraints

- Preserve `calculate_angle`, `classify_posture`, `hunchback-live`, and `hunchback-video` compatibility.
- The browser webcam is the primary experience; the CLI remains supported.
- Do not write frames, landmarks, calibration values, or session statistics to disk or a database.
- Bind the packaged server to `127.0.0.1` by default; Docker publishes it through an explicit port mapping.
- Keep browser code dependency-free and do not introduce a Node.js build step.
- Use non-diagnostic user-facing language and display a wellness-not-medical-advice notice.
- Reject WebSocket image payloads larger than 1,000,000 bytes and thresholds outside 60-180 degrees.
- Process at most one in-flight browser frame per connection.
- Use Python 3.12 for Docker and CI integration checks because native computer-vision wheels are the compatibility boundary.
- Keep implementation small, readable, typed, and split by a single clear responsibility per file.

---

## File Structure

- `src/hunchback_detection/posture.py`: validated geometry and posture result models.
- `src/hunchback_detection/vision.py`: MediaPipe lifecycle, landmark extraction, and frame analysis.
- `src/hunchback_detection/video_stream.py`: OpenCV CLI runtime using the shared analyzer.
- `src/hunchback_detection/web.py`: FastAPI routes, WebSocket validation, and app factory.
- `src/hunchback_detection/templates/index.html`: semantic application shell.
- `src/hunchback_detection/static/css/app.css`: responsive visual system.
- `src/hunchback_detection/static/js/{app,camera,connection,session,overlay}.js`: browser orchestration split by responsibility.
- `tests/{test_posture,test_vision,test_web,test_cli}.py`: deterministic Python tests.
- `tests/js/session.test.mjs`: browser-state unit tests with Node's built-in runner.
- `Dockerfile`, `.dockerignore`, `compose.yaml`: local container workflow.
- `README.md`, `AGENTS.md`, contributor and `docs/` files: product, architecture, privacy, calibration, troubleshooting, and development contracts.
- `.github/`: CI, dependency updates, issue forms, and pull-request template.

---

### Task 1: Repository Hygiene and Package Contract

**Files:**
- Create: `.gitignore`
- Modify: `pyproject.toml`
- Delete from Git: tracked `__pycache__/*.pyc`
- Test: `tests/test_package.py`

**Interfaces:**
- Consumes: existing `src/` package layout and console command names.
- Produces: installable extras `.[dev]`, `.[web]`, and `.[all]`; package data for templates/static assets; `hunchback-web` entry point.

- [ ] **Step 1: Write the failing metadata test**

```python
from importlib.metadata import entry_points


def test_console_scripts_are_registered() -> None:
    names = {item.name for item in entry_points(group="console_scripts")}
    assert {"hunchback-live", "hunchback-video", "hunchback-web"} <= names
```

- [ ] **Step 2: Run the focused test and confirm the missing web command**

Run: `python -m pytest tests/test_package.py -v`
Expected: FAIL because `hunchback-web` is not registered.

- [ ] **Step 3: Consolidate metadata and quality configuration**

Set `requires-python = ">=3.11,<3.13"`, retain the existing runtime dependencies, add FastAPI/Uvicorn/Pillow web dependencies, define dev dependencies for pytest/coverage/httpx/ruff/mypy/build, register `hunchback-web = "hunchback_detection.web:run_web_cli"`, include templates and static assets as package data, and configure Ruff, MyPy, and Pytest in `pyproject.toml`.

Create `.gitignore` entries for bytecode, virtual environments, IDE files, coverage, builds, local media outputs, and environment files. Remove all tracked bytecode with exact `git rm` paths, without touching source files.

- [ ] **Step 4: Install the editable development package in a Python 3.12 environment and run the test**

Run: `python -m pip install -e ".[all,dev]"` followed by `python -m pytest tests/test_package.py -v`
Expected: PASS and all three console scripts are discoverable.

- [ ] **Step 5: Commit the package contract**

```powershell
git add .gitignore pyproject.toml tests/test_package.py src tests
git commit -m "build: establish package and quality contract"
```

---

### Task 2: Validated Posture Domain

**Files:**
- Modify: `src/hunchback_detection/posture.py`
- Modify: `src/hunchback_detection/__init__.py`
- Modify: `tests/test_posture.py`

**Interfaces:**
- Consumes: two-dimensional numeric point sequences.
- Produces: `PostureStatus` enum; immutable `PostureResult(angle: float, status: PostureStatus)`; `validate_threshold(value: float) -> float`; existing public functions with preserved call shapes and string values.

- [ ] **Step 1: Add failing boundary and invalid-input tests**

```python
import pytest
from hunchback_detection.posture import calculate_angle, validate_threshold


@pytest.mark.parametrize("value", [59.9, 180.1, float("nan")])
def test_validate_threshold_rejects_invalid_values(value: float) -> None:
    with pytest.raises(ValueError):
        validate_threshold(value)


def test_calculate_angle_rejects_zero_length_vector() -> None:
    with pytest.raises(ValueError, match="distinct"):
        calculate_angle((0, 0), (0, 0), (1, 1))
```

- [ ] **Step 2: Run tests and confirm current permissive behavior fails them**

Run: `python -m pytest tests/test_posture.py -v`
Expected: FAIL because threshold validation is absent and zero-length vectors return 180.

- [ ] **Step 3: Implement explicit validation and typed status**

Use `PostureStatus(str, Enum)` with `GOOD = "good"` and `BAD = "bad"`, preserving the existing API values. Validate finite 2D points and finite thresholds in the inclusive 60-180 range. Keep `classify_posture` string-compatible through the `str` enum and export the new public types from `__init__.py`. The browser maps the internal `bad` value to the user-facing phrase “needs attention.”

- [ ] **Step 4: Run domain tests**

Run: `python -m pytest tests/test_posture.py -v`
Expected: PASS for right, straight, obtuse, threshold-boundary, invalid-threshold, invalid-point, and combined-analysis cases.

- [ ] **Step 5: Commit the validated domain**

```powershell
git add src/hunchback_detection/posture.py src/hunchback_detection/__init__.py tests/test_posture.py
git commit -m "feat: validate posture domain inputs"
```

---

### Task 3: Testable MediaPipe Frame Analyzer

**Files:**
- Create: `src/hunchback_detection/vision.py`
- Create: `tests/test_vision.py`

**Interfaces:**
- Consumes: BGR `numpy.ndarray` frames and a validated numeric threshold.
- Produces: `LandmarkPoint(x: float, y: float, visibility: float)`; `FrameAnalysis(detected: bool, angle: float | None, status: PostureStatus | None, landmarks: dict[str, LandmarkPoint])`; context-managed `PoseDetector.analyze(frame, threshold) -> FrameAnalysis`.

- [ ] **Step 1: Write tests against an injected fake pose model**

```python
def test_analyze_returns_no_pose_when_landmarks_are_absent(fake_pose_without_landmarks):
    detector = PoseDetector(pose_model=fake_pose_without_landmarks)
    result = detector.analyze(make_frame(), threshold=150)
    assert result.detected is False
    assert result.angle is None
    assert result.landmarks == {}


def test_analyze_maps_left_landmarks_to_pixels(fake_upright_pose):
    detector = PoseDetector(pose_model=fake_upright_pose)
    result = detector.analyze(make_frame(width=200, height=100), threshold=150)
    assert result.detected is True
    assert set(result.landmarks) == {"ear", "shoulder", "hip"}
```

- [ ] **Step 2: Run the new test and confirm the module is missing**

Run: `python -m pytest tests/test_vision.py -v`
Expected: FAIL with `ModuleNotFoundError: hunchback_detection.vision`.

- [ ] **Step 3: Implement the adapter and serializable results**

Lazy-import MediaPipe inside the default pose-model factory so domain imports remain lightweight. Convert BGR to RGB once, reject empty frames, check minimum landmark visibility, calculate pixel coordinates, call `analyze_points`, and close the pose model in `close()` and `__exit__()`.

- [ ] **Step 4: Run vision and domain tests**

Run: `python -m pytest tests/test_vision.py tests/test_posture.py -v`
Expected: PASS without webcam hardware.

- [ ] **Step 5: Commit the analyzer**

```powershell
git add src/hunchback_detection/vision.py tests/test_vision.py
git commit -m "feat: add testable pose frame analyzer"
```

---

### Task 4: FastAPI HTTP and WebSocket Service

**Files:**
- Create: `src/hunchback_detection/web.py`
- Create: `tests/test_web.py`

**Interfaces:**
- Consumes: WebSocket JSON `{"type":"frame","image":"<base64 JPEG>","threshold":<float>}`.
- Produces: `GET /`, `GET /health`, and `/ws/analyze`; success JSON `{"type":"analysis","detected":true,"angle":170.2,"status":"good","landmarks":{...}}`; safe error JSON `{"type":"error","code":"invalid_frame","message":"..."}`.

- [ ] **Step 1: Write failing route and protocol tests**

```python
def test_health_is_ready(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_websocket_rejects_unknown_message_type(client):
    with client.websocket_connect("/ws/analyze") as websocket:
        websocket.send_json({"type": "other"})
        assert websocket.receive_json()["code"] == "invalid_message"
```

- [ ] **Step 2: Run tests and confirm the web module is missing**

Run: `python -m pytest tests/test_web.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the app factory and bounded protocol**

Define `create_app(analyzer_factory: Callable[[], PoseDetector] = PoseDetector) -> FastAPI`. Validate JSON keys, base64 length, decoded byte length (maximum 1,000,000), JPEG decoding, and threshold. Create one analyzer per WebSocket connection and always close it in `finally`. Return safe protocol errors while keeping recoverable connections alive.

Define `run_web_cli()` with `--host` defaulting to `127.0.0.1` and `--port` defaulting to `8000`; call Uvicorn using the app factory.

- [ ] **Step 4: Run service tests**

Run: `python -m pytest tests/test_web.py -v`
Expected: PASS for page, health, no-pose, valid analysis, invalid JSON, invalid threshold, invalid image, oversized payload, and analyzer cleanup.

- [ ] **Step 5: Commit the service**

```powershell
git add src/hunchback_detection/web.py tests/test_web.py
git commit -m "feat: add live analysis web service"
```

---

### Task 5: Browser Camera, Calibration, and Session Experience

**Files:**
- Create: `src/hunchback_detection/templates/index.html`
- Create: `src/hunchback_detection/static/css/app.css`
- Create: `src/hunchback_detection/static/js/session.js`
- Create: `src/hunchback_detection/static/js/camera.js`
- Create: `src/hunchback_detection/static/js/connection.js`
- Create: `src/hunchback_detection/static/js/overlay.js`
- Create: `src/hunchback_detection/static/js/app.js`
- Create: `tests/js/session.test.mjs`
- Modify: `tests/test_web.py`

**Interfaces:**
- Consumes: browser MediaDevices stream and Task 4 WebSocket protocol.
- Produces: `Calibration(samplesRequired=30, offsetDegrees=12)` with `add(angle)`, `ready`, `progress`, `baseline`, and bounded `threshold`; `SessionMetrics.update(status, timestamp)` with `sessionSeconds`, `attentionSeconds`, and `goodPercentage`.

- [ ] **Step 1: Write failing JavaScript state tests**

```javascript
import test from "node:test";
import assert from "node:assert/strict";
import { Calibration, SessionMetrics } from "../../src/hunchback_detection/static/js/session.js";

test("calibration uses the median and a bounded offset", () => {
  const calibration = new Calibration(3, 12);
  [170, 160, 165].forEach((angle) => calibration.add(angle));
  assert.equal(calibration.baseline, 165);
  assert.equal(calibration.threshold, 153);
});

test("session counts only intervals with valid posture", () => {
  const metrics = new SessionMetrics();
  metrics.update("good", 1000);
  metrics.update("bad", 2000);
  metrics.update(null, 3000);
  assert.equal(metrics.sessionSeconds, 2);
  assert.equal(metrics.attentionSeconds, 1);
  assert.equal(metrics.goodPercentage, 50);
});
```

- [ ] **Step 2: Run tests and confirm the module is missing**

Run: `node --test tests/js/session.test.mjs`
Expected: FAIL because `session.js` does not exist.

- [ ] **Step 3: Implement state logic and the semantic page shell**

Implement median-based calibration, clamp its threshold to 60-180, ignore non-finite samples, and track only valid intervals capped at two seconds to prevent background-tab jumps. Build accessible markup with a skip link, live status region, start/stop/recalibrate controls, mirrored video, canvas overlay, four metric cards, privacy statement, and medical disclaimer.

- [ ] **Step 4: Implement camera, transport, overlay, and orchestration modules**

Capture at 640x480 maximum and target 5 analysis frames per second. Send a new frame only after the prior analysis/error response. Stop all media tracks and close the socket on stop/unload. Draw returned landmark segments on the overlay and show explicit idle, permission, connecting, calibrating, good, needs-attention, no-pose, disconnected, and error states.

- [ ] **Step 5: Add static-asset integration assertions and run frontend/backend tests**

Run: `node --test tests/js/session.test.mjs` and `python -m pytest tests/test_web.py -v`
Expected: PASS; the HTML references local CSS and ES-module assets and contains no external scripts.

- [ ] **Step 6: Commit the browser experience**

```powershell
git add src/hunchback_detection/templates src/hunchback_detection/static tests/js tests/test_web.py
git commit -m "feat: build live browser posture experience"
```

---

### Task 6: CLI Integration and Resource Safety

**Files:**
- Modify: `src/hunchback_detection/video_stream.py`
- Modify: `scripts/run_live.py`
- Modify: `scripts/run_video.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: Task 3 `PoseDetector`; webcam index or input video path; threshold; optional output path.
- Produces: existing console behavior, validated CLI options, consistent status labels, nonzero failure exits, and deterministic resource cleanup.

- [ ] **Step 1: Write failure-path and cleanup tests**

```python
def test_run_video_rejects_missing_input(tmp_path):
    missing = tmp_path / "missing.mp4"
    with pytest.raises(FileNotFoundError, match="missing.mp4"):
        run_video(str(missing))


def test_run_stream_releases_capture_when_analysis_fails(
    fake_capture, failing_detector
):
    with pytest.raises(RuntimeError):
        run_stream(fake_capture, detector=failing_detector)
    assert fake_capture.released is True
```

- [ ] **Step 2: Run tests and confirm missing validation/injection**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL because the current stream owns MediaPipe directly and does not validate paths first.

- [ ] **Step 3: Refactor the stream around the shared analyzer**

Accept an injectable detector, validate inputs before opening them, use `try/finally` for capture/writer/window cleanup, check writer creation, preserve `q`/Escape exit, and render the new status vocabulary. Keep wrappers thin and existing command flags compatible.

- [ ] **Step 4: Run all Python tests**

Run: `python -m pytest -v`
Expected: PASS without accessing a physical camera.

- [ ] **Step 5: Commit CLI integration**

```powershell
git add src/hunchback_detection/video_stream.py scripts tests/test_cli.py
git commit -m "refactor: share analysis engine with cli"
```

---

### Task 7: Reproducible Docker Runtime

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `compose.yaml`
- Modify: `tests/test_package.py`

**Interfaces:**
- Consumes: installable package and `hunchback-web` command.
- Produces: OCI image exposing port 8000, running as non-root, with `/health` container health check; Compose service reachable at `http://localhost:8000`.

- [ ] **Step 1: Add a package smoke test for app creation**

```python
def test_web_app_can_be_created() -> None:
    from hunchback_detection.web import create_app

    assert create_app().title == "Posture Coach"
```

- [ ] **Step 2: Run the test before container work**

Run: `python -m pytest tests/test_package.py -v`
Expected: PASS, establishing the application import contract used by the image.

- [ ] **Step 3: Create the container files**

Use `python:3.12-slim`, install only required OpenCV runtime libraries, install the package without dev dependencies, create an unprivileged `app` user, expose 8000, add a Python-standard-library health check, and run `hunchback-web --host 0.0.0.0 --port 8000`. Compose maps `127.0.0.1:8000:8000`, uses `init: true`, and sets `read_only: true` with a writable `/tmp` tmpfs.

- [ ] **Step 4: Build and verify the container**

Run: `docker compose build`, `docker compose up -d`, poll `http://127.0.0.1:8000/health`, then run `docker compose down`.
Expected: image builds, container becomes healthy, response is `{"status":"ok"}`, and shutdown removes only Compose-managed resources.

- [ ] **Step 5: Commit Docker support**

```powershell
git add Dockerfile .dockerignore compose.yaml tests/test_package.py
git commit -m "build: add hardened local Docker runtime"
```

---

### Task 8: Documentation and GitHub Project Operations

**Files:**
- Modify: `README.md`
- Create: `AGENTS.md`
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`
- Create: `CHANGELOG.md`
- Create: `docs/architecture.md`
- Create: `docs/privacy.md`
- Create: `docs/calibration.md`
- Create: `docs/troubleshooting.md`
- Create: `docs/development.md`
- Create: `.github/workflows/ci.yml`
- Create: `.github/dependabot.yml`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/pull_request_template.md`

**Interfaces:**
- Consumes: verified commands, endpoints, architecture, limitations, and quality tooling from Tasks 1-7.
- Produces: accurate newcomer, contributor, security, automation, and agent-facing contracts.

- [ ] **Step 1: Add a documentation contract test**

```python
@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "docs/architecture.md",
        "docs/privacy.md",
        "docs/calibration.md",
        "docs/troubleshooting.md",
        "docs/development.md",
    ],
)
def test_required_document_exists(path: str) -> None:
    assert Path(path).is_file()
```

- [ ] **Step 2: Run the contract and confirm missing documents**

Run: `python -m pytest tests/test_package.py -v`
Expected: FAIL listing the documentation files that do not exist yet.

- [ ] **Step 3: Write documentation from verified behavior**

Rewrite the README around product value, the verified application preview, one-command Docker start, native installation, web/CLI usage, architecture, privacy, calibration, limitations, testing, roadmap, contributing, security, and license. Correct the existing accidental `andsdsd` text. Write each supporting document with exact commands and no unsupported medical-performance claims.

Write `AGENTS.md` with repository map, Python/JavaScript style rules, privacy invariants, dependency boundaries, exact quality commands, manual-camera limitation, and the rule that frames must never be persisted.

- [ ] **Step 4: Add GitHub automation and templates**

Configure CI jobs for Ruff, MyPy, Pytest/coverage, Node built-in tests, package build, and Docker build on Python 3.11/3.12 where applicable. Add weekly Dependabot updates for pip, Docker, and GitHub Actions. Add structured bug/feature issue forms and a pull request checklist covering tests, privacy, docs, and screenshots.

- [ ] **Step 5: Validate documentation and workflow syntax**

Run: `python -m pytest tests/test_package.py -v`, `python -m build`, and parse all YAML files with a safe YAML loader.
Expected: PASS; package README renders as metadata and documented commands match existing scripts.

- [ ] **Step 6: Commit documentation and repository operations**

```powershell
git add README.md AGENTS.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md CHANGELOG.md docs .github tests/test_package.py
git commit -m "docs: complete project and contributor experience"
```

---

### Task 9: Full Verification, Browser Evidence, and Release Push

**Files:**
- Modify only if verification reveals a defect: files owned by Tasks 1-8.
- Create: `docs/assets/posture-coach-preview.png` after browser verification.

**Interfaces:**
- Consumes: the complete repository.
- Produces: passing evidence, clean Git status, polished preview asset, and pushed `main` branch.

- [ ] **Step 1: Run deterministic quality gates**

Run: `python -m ruff format --check .`, `python -m ruff check .`, `python -m mypy src`, `python -m pytest --cov=hunchback_detection --cov-report=term-missing --cov-fail-under=85`, `node --test tests/js/session.test.mjs`, and `python -m build`.
Expected: every command exits 0; fix root causes and rerun the failed command plus the full suite.

- [ ] **Step 2: Run container integration verification**

Run: `docker compose build`, `docker compose up -d`, verify the health endpoint and page response, inspect container health/non-root identity, then `docker compose down`.
Expected: healthy local service, HTTP 200 page, non-root process, and clean shutdown.

- [ ] **Step 3: Exercise the app in a real browser**

Verify responsive layout, start/stop controls, permission-denied state, WebSocket connection, calibration progress, no-pose state, live metrics, keyboard focus, and no external network/storage activity. If camera access is unavailable in the automation environment, record that exact manual limitation rather than claiming it passed. Capture `docs/assets/posture-coach-preview.png` from the verified page and link it from the README.

- [ ] **Step 4: Audit repository and commits**

Run: `git diff --check`, `git status --short`, `git ls-files | rg "(__pycache__|\.pyc$|\.env$)"`, `git log --oneline --decorate -10`, and inspect `git diff origin/main...HEAD --stat`.
Expected: no generated files or secrets, no unexplained working-tree changes, and only intended commits/files.

- [ ] **Step 5: Commit final verification fixes and preview**

```powershell
git add docs/assets/posture-coach-preview.png README.md
git commit -m "docs: add verified application preview"
```

- [ ] **Step 6: Synchronize and push safely**

Run: `git fetch origin`, verify `main` has not diverged unexpectedly, use `git pull --ff-only origin main` only if simply behind, rerun the minimum post-sync checks, then `git push origin main`.
Expected: `main` is pushed successfully and `git status --short --branch` reports it aligned with `origin/main`.
