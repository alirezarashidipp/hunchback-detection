# Development guide

## Prerequisites

- Python 3.11 or 3.12
- Node.js 20 or newer for JavaScript tests
- Docker Desktop for the release-equivalent runtime check

Install the editable package and development tools:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run locally

```bash
hunchback-web --host 127.0.0.1 --port 8000
```

The `/health` endpoint returns `{"status":"ok"}`. The web UI is served at `/`
and live analysis uses `/ws/analyze`.

## Required checks

Run these commands before opening a pull request:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest --cov=hunchback_detection --cov-report=term-missing --cov-fail-under=85
node --test tests/js/*.test.mjs
python -m build
docker compose build
```

Run the app in a real browser at 320, 375, 768, and 1280 pixel widths for UI
changes. Exercise successful camera permission when a device is available and
the permission-denied recovery path in every release.

## Testing boundaries

- Geometry tests use exact, deterministic points.
- Vision tests inject a fake pose model; they do not require camera hardware.
- Web tests inject a fake analyzer and exercise valid and invalid WebSocket
  messages.
- JavaScript tests cover calibration and session timing without a browser.
- Docker verification constructs a real MediaPipe detector against a blank
  frame to catch binary and dependency incompatibilities.

## Release checklist

1. Confirm every required check passes from a clean checkout.
2. Run `docker compose up -d` and wait for the container to become healthy.
3. Confirm the container user is non-root and the real detector initializes.
4. Review `docs/privacy.md` against the actual data flow.
5. Update `CHANGELOG.md`, version metadata, and screenshots when relevant.
