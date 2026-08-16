"""Local FastAPI service for live in-memory posture analysis."""

from __future__ import annotations

import argparse
import base64
import binascii
import io
import json
from collections.abc import Callable
from typing import Any, Protocol

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from PIL import Image, UnidentifiedImageError

from .posture import validate_threshold
from .vision import FrameAnalysis, PoseDetector

MAX_IMAGE_BYTES = 1_000_000
MAX_MESSAGE_CHARACTERS = 1_400_000
JPEG_DATA_PREFIX = "data:image/jpeg;base64,"


class Analyzer(Protocol):
    """Frame analyzer contract used by each WebSocket connection."""

    def analyze(self, frame: np.ndarray, threshold: float) -> FrameAnalysis: ...

    def close(self) -> None: ...


AnalyzerFactory = Callable[[], Analyzer]


def _error(code: str, message: str) -> dict[str, str]:
    return {"type": "error", "code": code, "message": message}


def _decode_frame(image_value: object) -> np.ndarray:
    if not isinstance(image_value, str) or not image_value.startswith(
        JPEG_DATA_PREFIX
    ):
        raise ValueError("image must be a JPEG data URL")

    encoded = image_value.removeprefix(JPEG_DATA_PREFIX)
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("image contains invalid base64 data") from error

    if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("image must contain at most 1000000 bytes")

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            if image.format != "JPEG":
                raise ValueError("image must use JPEG encoding")
            rgb_frame = np.asarray(image.convert("RGB"), dtype=np.uint8)
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError("image could not be decoded") from error

    return np.ascontiguousarray(rgb_frame[:, :, ::-1])


def _analysis_message(result: FrameAnalysis) -> dict[str, Any]:
    landmarks = {
        name: {
            "x": point.x,
            "y": point.y,
            "visibility": point.visibility,
        }
        for name, point in result.landmarks.items()
    }
    return {
        "type": "analysis",
        "detected": result.detected,
        "angle": result.angle,
        "status": result.status.value if result.status is not None else None,
        "landmarks": landmarks,
    }


async def _handle_connection(
    websocket: WebSocket,
    analyzer_factory: AnalyzerFactory,
) -> None:
    await websocket.accept()
    analyzer = analyzer_factory()
    try:
        while True:
            raw_message = await websocket.receive_text()
            if len(raw_message) > MAX_MESSAGE_CHARACTERS:
                await websocket.send_json(
                    _error("frame_too_large", "frame message is too large")
                )
                continue

            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json(
                    _error("invalid_message", "message must be valid JSON")
                )
                continue

            if not isinstance(message, dict) or message.get("type") != "frame":
                await websocket.send_json(
                    _error("invalid_message", "expected a frame message")
                )
                continue

            try:
                threshold = validate_threshold(message.get("threshold", 160.0))
            except (TypeError, ValueError):
                await websocket.send_json(
                    _error(
                        "invalid_threshold",
                        "threshold must be between 60 and 180 degrees",
                    )
                )
                continue

            try:
                frame = _decode_frame(message.get("image"))
            except ValueError as error:
                await websocket.send_json(_error("invalid_frame", str(error)))
                continue

            try:
                result = analyzer.analyze(frame, threshold)
            except Exception:
                await websocket.send_json(
                    _error("analysis_failed", "frame analysis failed")
                )
                continue

            await websocket.send_json(_analysis_message(result))
    except WebSocketDisconnect:
        pass
    finally:
        analyzer.close()


def create_app(analyzer_factory: AnalyzerFactory = PoseDetector) -> FastAPI:
    """Build the web application with an injectable analyzer boundary."""
    app = FastAPI(
        title="Posture Coach",
        description="Local-first live posture feedback",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def home() -> str:
        return "<main><h1>Posture Coach</h1></main>"

    @app.websocket("/ws/analyze")
    async def analyze_websocket(websocket: WebSocket) -> None:
        await _handle_connection(websocket, analyzer_factory)

    return app


app = create_app()


def run_web_cli() -> None:
    """Run the local web application from the installed console command."""
    parser = argparse.ArgumentParser(description="Run the local Posture Coach app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run("hunchback_detection.web:app", host=args.host, port=args.port)
