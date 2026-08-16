import { CameraController } from "./camera.js";
import { AnalysisConnection } from "./connection.js";
import { PoseOverlay } from "./overlay.js";
import { Calibration, SessionMetrics } from "./session.js";

const FRAME_INTERVAL_MS = 200;

const elements = {
  video: document.querySelector("#camera-video"),
  overlay: document.querySelector("#pose-overlay"),
  stage: document.querySelector("#camera-stage"),
  start: document.querySelector("#start-button"),
  stop: document.querySelector("#stop-button"),
  recalibrate: document.querySelector("#calibrate-button"),
  connection: document.querySelector("#connection-state"),
  status: document.querySelector("#status-readout"),
  statusText: document.querySelector("#status-text"),
  calibrationProgress: document.querySelector("#calibration-progress"),
  calibrationBar: document.querySelector("#calibration-bar"),
  calibrationText: document.querySelector("#calibration-text"),
  angle: document.querySelector("#angle-value"),
  threshold: document.querySelector("#threshold-value"),
  good: document.querySelector("#good-value"),
  attention: document.querySelector("#attention-value"),
};

const camera = new CameraController(elements.video);
const overlay = new PoseOverlay(elements.overlay);
const calibration = new Calibration();
const metrics = new SessionMetrics();

let connection = null;
let captureTimer = null;
let running = false;

function setConnectionState(state) {
  const labels = {
    connecting: "Connecting",
    connected: "Local service ready",
    disconnected: running ? "Disconnected" : "Offline",
    error: "Connection failed",
  };
  elements.connection.dataset.state = state;
  elements.connection.textContent = labels[state] || "Offline";
}

function setStatus(state, message) {
  elements.status.dataset.state = state;
  elements.statusText.textContent = message;
}

function formatDuration(seconds) {
  const wholeSeconds = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(wholeSeconds / 60);
  const remainder = wholeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function renderMetrics(angle = null) {
  elements.angle.textContent = angle === null ? "—" : `${angle.toFixed(1)}°`;
  elements.threshold.textContent = calibration.ready
    ? `${calibration.threshold.toFixed(1)}°`
    : "—";
  elements.good.textContent = `${Math.round(metrics.goodPercentage)}%`;
  elements.attention.textContent = formatDuration(metrics.attentionSeconds);
}

function renderCalibration() {
  const percentage = Math.round(calibration.progress * 100);
  elements.calibrationProgress.setAttribute("aria-valuenow", String(percentage));
  elements.calibrationBar.style.transform = `scaleX(${calibration.progress})`;

  if (calibration.ready) {
    elements.calibrationText.textContent = "Calibration complete. Keep your side profile visible.";
    return;
  }
  elements.calibrationText.textContent = `Sit upright while calibration samples your baseline — ${percentage}%`;
}

function handleAnalysis(message) {
  if (!message.detected) {
    overlay.clear();
    metrics.update(null);
    setStatus("idle", "No side profile detected");
    elements.calibrationText.textContent = "Keep your ear, shoulder, and hip visible.";
    return;
  }

  overlay.draw(message.landmarks);
  if (!calibration.ready) {
    calibration.add(message.angle);
    setStatus("idle", "Calibrating your upright position");
    renderCalibration();
    renderMetrics(message.angle);
    return;
  }

  metrics.update(message.status);
  const needsAttention = message.status === "bad";
  setStatus(
    needsAttention ? "bad" : "good",
    needsAttention ? "Posture needs attention" : "Posture is on target",
  );
  renderMetrics(message.angle);
}

function handleAnalysisError(message) {
  setStatus("error", message);
}

function scheduleCapture() {
  window.clearTimeout(captureTimer);
  if (!running) {
    return;
  }

  const capture = camera.capture();
  if (capture) {
    overlay.resize(capture.width, capture.height);
    const threshold = calibration.ready ? calibration.threshold : 60;
    connection.sendFrame(capture.image, threshold);
  }
  captureTimer = window.setTimeout(scheduleCapture, FRAME_INTERVAL_MS);
}

async function startCamera() {
  if (running) {
    return;
  }
  elements.start.disabled = true;
  elements.start.dataset.state = "loading";
  elements.start.textContent = "Starting camera";
  setStatus("idle", "Waiting for camera permission");

  try {
    await camera.start();
    connection = new AnalysisConnection({
      onAnalysis: handleAnalysis,
      onError: handleAnalysisError,
      onStateChange: setConnectionState,
    });
    await connection.connect();
    running = true;
    elements.stage.dataset.active = "true";
    elements.stop.disabled = false;
    elements.recalibrate.disabled = false;
    elements.start.textContent = "Camera active";
    renderCalibration();
    scheduleCapture();
  } catch (error) {
    camera.stop();
    connection?.close();
    connection = null;
    elements.start.disabled = false;
    elements.start.dataset.state = "error";
    elements.start.textContent = "Try camera again";
    setConnectionState("error");
    setStatus("error", error.message || "Camera access failed. Check browser permission and retry.");
  } finally {
    if (running) {
      delete elements.start.dataset.state;
    }
  }
}

function stopCamera() {
  running = false;
  window.clearTimeout(captureTimer);
  camera.stop();
  connection?.close();
  connection = null;
  overlay.clear();
  elements.stage.dataset.active = "false";
  elements.start.disabled = false;
  elements.start.textContent = "Start camera";
  elements.stop.disabled = true;
  elements.recalibrate.disabled = true;
  setConnectionState("disconnected");
  setStatus("idle", "Camera is off");
}

function recalibrate() {
  calibration.reset();
  metrics.reset();
  renderMetrics();
  renderCalibration();
  setStatus("idle", "Calibrating your upright position");
}

elements.start.addEventListener("click", startCamera);
elements.stop.addEventListener("click", stopCamera);
elements.recalibrate.addEventListener("click", recalibrate);
window.addEventListener("pagehide", stopCamera);
