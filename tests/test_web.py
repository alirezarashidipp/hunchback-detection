"""HTTP and WebSocket contract tests for the local web application."""

from __future__ import annotations

import base64
import io
from collections.abc import Iterator

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from hunchback_detection.posture import PostureStatus
from hunchback_detection.vision import FrameAnalysis, LandmarkPoint


class FakeDetector:
    def __init__(self, result: FrameAnalysis) -> None:
        self.result = result
        self.received_threshold: float | None = None
        self.closed = False

    def analyze(self, frame: np.ndarray, threshold: float) -> FrameAnalysis:
        assert frame.shape == (2, 3, 3)
        self.received_threshold = threshold
        return self.result

    def close(self) -> None:
        self.closed = True


def jpeg_data_url() -> str:
    image = Image.new("RGB", (3, 2), color=(40, 80, 120))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


@pytest.fixture
def detector_pool() -> list[FakeDetector]:
    return []


@pytest.fixture
def client(detector_pool: list[FakeDetector]) -> Iterator[TestClient]:
    from hunchback_detection.web import create_app

    result = FrameAnalysis(
        detected=True,
        angle=172.5,
        status=PostureStatus.GOOD,
        landmarks={
            "ear": LandmarkPoint(10, 20, 0.9),
            "shoulder": LandmarkPoint(20, 40, 0.9),
            "hip": LandmarkPoint(30, 60, 0.9),
        },
    )

    def detector_factory() -> FakeDetector:
        detector = FakeDetector(result)
        detector_pool.append(detector)
        return detector

    with TestClient(create_app(analyzer_factory=detector_factory)) as test_client:
        yield test_client


def test_health_is_ready(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_identifies_the_product(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Posture Coach" in response.text


def test_websocket_rejects_unknown_message_type(client: TestClient) -> None:
    with client.websocket_connect("/ws/analyze") as websocket:
        websocket.send_json({"type": "other"})

        message = websocket.receive_json()

    assert message["type"] == "error"
    assert message["code"] == "invalid_message"


def test_websocket_rejects_threshold_outside_safe_range(client: TestClient) -> None:
    with client.websocket_connect("/ws/analyze") as websocket:
        websocket.send_json(
            {"type": "frame", "image": jpeg_data_url(), "threshold": 20}
        )

        message = websocket.receive_json()

    assert message["code"] == "invalid_threshold"


def test_websocket_returns_serializable_analysis(
    client: TestClient,
    detector_pool: list[FakeDetector],
) -> None:
    with client.websocket_connect("/ws/analyze") as websocket:
        websocket.send_json(
            {"type": "frame", "image": jpeg_data_url(), "threshold": 150}
        )

        message = websocket.receive_json()

    assert message == {
        "type": "analysis",
        "detected": True,
        "angle": 172.5,
        "status": "good",
        "landmarks": {
            "ear": {"x": 10, "y": 20, "visibility": 0.9},
            "shoulder": {"x": 20, "y": 40, "visibility": 0.9},
            "hip": {"x": 30, "y": 60, "visibility": 0.9},
        },
    }
    assert detector_pool[0].received_threshold == 150


def test_websocket_closes_detector_after_disconnect(
    client: TestClient,
    detector_pool: list[FakeDetector],
) -> None:
    with client.websocket_connect("/ws/analyze"):
        pass

    assert detector_pool[0].closed is True
