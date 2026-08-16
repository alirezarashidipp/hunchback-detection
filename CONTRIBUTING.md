# Contributing

Thank you for improving Posture Coach. Small, focused changes are easiest to
review and safest for a camera-based application.

## Setup

Use Python 3.11 or 3.12 and Node.js 20 or newer.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Development workflow

1. Open an issue for a substantial feature or behavioral change.
2. Create a focused branch from `main`.
3. Add a failing test that demonstrates the required behavior.
4. Implement the smallest readable change that makes it pass.
5. Run every check listed in `docs/development.md`.
6. Update documentation for changed commands, contracts, or limitations.
7. Open a pull request using the repository template.

Use imperative commit subjects such as `feat: add calibration reset`. Keep
generated files, recordings, and unrelated formatting out of the change.

## Product guardrails

- Images and session measurements remain ephemeral by default.
- User-facing copy must not make medical claims.
- Changes must preserve keyboard access, responsive behavior, and reduced-motion
  preferences.
- New dependencies need a concrete runtime or maintenance benefit.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
