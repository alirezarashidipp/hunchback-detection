const MIN_THRESHOLD = 60;
const MAX_THRESHOLD = 180;
const MAX_INTERVAL_SECONDS = 2;

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function median(values) {
  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 1) {
    return sorted[middle];
  }
  return (sorted[middle - 1] + sorted[middle]) / 2;
}

export class Calibration {
  constructor(samplesRequired = 30, offsetDegrees = 12) {
    if (!Number.isInteger(samplesRequired) || samplesRequired < 1) {
      throw new RangeError("samplesRequired must be a positive integer");
    }
    if (!Number.isFinite(offsetDegrees) || offsetDegrees < 0) {
      throw new RangeError("offsetDegrees must be a non-negative number");
    }
    this.samplesRequired = samplesRequired;
    this.offsetDegrees = offsetDegrees;
    this.samples = [];
  }

  add(angle) {
    if (!Number.isFinite(angle) || this.ready) {
      return;
    }
    this.samples.push(angle);
  }

  reset() {
    this.samples = [];
  }

  get ready() {
    return this.samples.length >= this.samplesRequired;
  }

  get progress() {
    return Math.min(1, this.samples.length / this.samplesRequired);
  }

  get baseline() {
    if (!this.ready) {
      return null;
    }
    return median(this.samples);
  }

  get threshold() {
    if (!this.ready) {
      return MAX_THRESHOLD;
    }
    return clamp(
      this.baseline - this.offsetDegrees,
      MIN_THRESHOLD,
      MAX_THRESHOLD,
    );
  }
}

export class SessionMetrics {
  constructor() {
    this.reset();
  }

  update(status, timestamp = performance.now()) {
    if (this.previousTimestamp !== null && this.previousStatus !== null) {
      const elapsed = clamp(
        (timestamp - this.previousTimestamp) / 1000,
        0,
        MAX_INTERVAL_SECONDS,
      );
      this.sessionSeconds += elapsed;
      if (this.previousStatus === "bad") {
        this.attentionSeconds += elapsed;
      }
    }

    this.previousStatus = status === "good" || status === "bad" ? status : null;
    this.previousTimestamp = timestamp;
  }

  reset() {
    this.sessionSeconds = 0;
    this.attentionSeconds = 0;
    this.previousStatus = null;
    this.previousTimestamp = null;
  }

  get goodPercentage() {
    if (this.sessionSeconds === 0) {
      return 0;
    }
    return ((this.sessionSeconds - this.attentionSeconds) / this.sessionSeconds) * 100;
  }
}
