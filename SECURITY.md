# Security policy

## Supported versions

Security fixes are applied to the latest version on `main`.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting feature for this repository.
Do not open a public issue for an unpatched vulnerability. Include the affected
component, reproduction steps, impact, and any suggested mitigation. You should
receive an acknowledgement within seven days.

## Security and privacy model

The default deployment binds to localhost, runs as a non-root container user,
uses a read-only filesystem, and stores neither camera frames nor session
measurements. Browser frames are sent to the local FastAPI process over a
WebSocket for in-memory analysis.

This design does not make an internet-exposed deployment safe by itself. If you
place the app behind a network-accessible proxy, add HTTPS, authentication,
request limits, origin controls, and appropriate monitoring.
