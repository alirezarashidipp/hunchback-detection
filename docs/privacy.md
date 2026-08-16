# Privacy model

Posture Coach is local-first by design. Its default Docker and native commands
perform pose analysis on the same computer that owns the camera.

## What is processed

The browser captures a downscaled JPEG frame and sends it over a WebSocket to
the local FastAPI service. The service decodes the frame, extracts three pose
landmarks, calculates an angle, returns the result, and releases the frame.

## What is retained

Nothing is intentionally persisted by the web application:

- no camera image or video recording;
- no landmark history on the server;
- no database, analytics SDK, cookies, or account;
- no server-side session profile;
- no browser local storage or indexed database.

Calibration samples and session totals exist only in the page's JavaScript
memory. Refreshing or closing the page clears them. Normal process and network
buffers may hold data briefly while a frame is being handled.

## Network boundary

Docker Compose binds the service to `127.0.0.1:8000`, so other machines cannot
connect through the host network by default. Native `hunchback-web` also binds
to `127.0.0.1` unless a different host is explicitly supplied.

Changing the bind address, adding a reverse proxy, or deploying to a remote
server changes this privacy model. Such deployments need HTTPS, authentication,
origin validation, retention decisions, and clear user consent.

## Logs

The application does not log frame payloads, landmarks, angles, or session
statistics. The web server may log request paths, status codes, and connection
metadata to standard output. Operators control those runtime logs.

## Verify the contract

Search the browser code for storage or telemetry APIs and inspect container
mounts before a release. The automated tests also verify bounded messages and
safe WebSocket errors, but privacy review remains required for any new capture,
logging, persistence, or network feature.
