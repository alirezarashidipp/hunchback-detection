import test from "node:test";
import assert from "node:assert/strict";

import {
  Calibration,
  SessionMetrics,
} from "../../src/hunchback_detection/static/js/session.js";

test("calibration uses the median and a bounded offset", () => {
  const calibration = new Calibration(3, 12);

  [170, 160, 165].forEach((angle) => calibration.add(angle));

  assert.equal(calibration.ready, true);
  assert.equal(calibration.progress, 1);
  assert.equal(calibration.baseline, 165);
  assert.equal(calibration.threshold, 153);
});

test("calibration ignores invalid samples", () => {
  const calibration = new Calibration(2, 12);

  [Number.NaN, null, 170].forEach((angle) => calibration.add(angle));

  assert.equal(calibration.ready, false);
  assert.equal(calibration.progress, 0.5);
});

test("calibration threshold stays inside the backend contract", () => {
  const calibration = new Calibration(1, 200);

  calibration.add(80);

  assert.equal(calibration.threshold, 60);
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

test("session caps background-tab time jumps", () => {
  const metrics = new SessionMetrics();

  metrics.update("bad", 1000);
  metrics.update("bad", 11000);

  assert.equal(metrics.sessionSeconds, 2);
  assert.equal(metrics.attentionSeconds, 2);
});

test("session reset clears every derived value", () => {
  const metrics = new SessionMetrics();
  metrics.update("bad", 1000);
  metrics.update("bad", 2000);

  metrics.reset();

  assert.equal(metrics.sessionSeconds, 0);
  assert.equal(metrics.attentionSeconds, 0);
  assert.equal(metrics.goodPercentage, 0);
});
