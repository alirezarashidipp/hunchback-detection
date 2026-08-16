# Troubleshooting

## The browser does not offer camera permission

Camera access requires `localhost` or HTTPS. Open the site at
`http://localhost:8000`, check the browser's site permissions, close other apps
using the camera, and select **Try camera again**.

## No pose is detected

Use a side view with the left ear, shoulder, and hip visible. Improve lighting,
move farther from the camera, and remove objects that obscure the upper body.
Recalibrate after changing the camera position.

## Docker cannot bind port 8000

Another process is already using the port. Stop that process or change the host
side of the mapping in `compose.yaml`, for example `127.0.0.1:8080:8000`, then
open `http://localhost:8080`.

## Docker health check fails

Inspect the service state and logs:

```bash
docker compose ps
docker compose logs posture-coach
```

Rebuild after dependency changes with `docker compose build --no-cache`, then
start the service again.

## Native installation fails

Confirm `python --version` reports 3.11 or 3.12. The pinned MediaPipe build does
not support every newer Python release. Prefer the Docker workflow when the host
Python version is outside the supported range.

## OpenCV CLI window is blank or unavailable

The web app is the recommended interface. CLI preview windows require a desktop
session and local camera access; they generally do not work inside the provided
container. Verify the input path, camera index, and operating-system camera
permission when running natively.
