export class PoseOverlay {
  constructor(canvas) {
    this.canvas = canvas;
    this.context = canvas.getContext("2d");
  }

  resize(width, height) {
    if (this.canvas.width === width && this.canvas.height === height) {
      return;
    }
    this.canvas.width = width;
    this.canvas.height = height;
  }

  clear() {
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  draw(landmarks) {
    this.clear();
    const ear = landmarks?.ear;
    const shoulder = landmarks?.shoulder;
    const hip = landmarks?.hip;
    if (!ear || !shoulder || !hip) {
      return;
    }

    const styles = getComputedStyle(document.documentElement);
    const lineColor = styles.getPropertyValue("--color-accent").trim();
    const pointColor = styles.getPropertyValue("--color-graphite-ink").trim();

    this.context.strokeStyle = lineColor;
    this.context.lineWidth = 3;
    this.context.lineCap = "round";
    this.context.beginPath();
    this.context.moveTo(ear.x, ear.y);
    this.context.lineTo(shoulder.x, shoulder.y);
    this.context.lineTo(hip.x, hip.y);
    this.context.stroke();

    this.context.fillStyle = pointColor;
    [ear, shoulder, hip].forEach((point) => {
      this.context.beginPath();
      this.context.arc(point.x, point.y, 5, 0, Math.PI * 2);
      this.context.fill();
    });
  }
}
