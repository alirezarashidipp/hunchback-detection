# Repository guide

## Working loop

1. Read `README.md` and the module or document you will change.
2. Preserve the local-first contract: analyze frames in memory and keep session
   data in the browser.
3. Add or update a focused test before changing behavior.
4. Keep data flow explicit and modules small; prefer plain functions over new
   layers.
5. Run the narrow test, then the full checks in `docs/development.md`.
6. Update user-facing documentation when commands, behavior, or limitations
   change. Work is complete only when every relevant check passes.

## Boundaries

- Treat this as an educational wellness tool. Use observational language and
  avoid diagnosis or medical claims.
- Support Python 3.11–3.12. `mediapipe==0.10.21` is intentional because the
  detector uses its `solutions` API.
- Keep browser code framework-free and split by responsibility under
  `src/hunchback_detection/static/js/`.
- Maintain keyboard access, visible focus, reduced-motion support, and layouts
  from 320 px upward.
- Keep secrets, recordings, generated video, virtual environments, caches, and
  browser artifacts out of Git.

## Context pointers

- Read `docs/architecture.md` when changing module boundaries, WebSocket data,
  frame processing, or state ownership.
- Read `docs/privacy.md` when changing capture, transport, storage, logging, or
  deployment behavior.
- Read `docs/calibration.md` when changing thresholds, sampling, posture state,
  or session metrics.
- Read `CONTRIBUTING.md` for commit, test, and pull-request expectations.
