const MAX_CAPTURE_WIDTH = 640;
const JPEG_QUALITY = 0.72;

export class CameraController {
  constructor(videoElement) {
    this.videoElement = videoElement;
    this.captureCanvas = document.createElement("canvas");
    this.stream = null;
  }

  async start() {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("This browser does not provide camera access.");
    }

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        facingMode: "user",
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
    });
    this.videoElement.srcObject = this.stream;
    await this.videoElement.play();
  }

  stop() {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.videoElement.srcObject = null;
  }

  capture() {
    const sourceWidth = this.videoElement.videoWidth;
    const sourceHeight = this.videoElement.videoHeight;
    if (!sourceWidth || !sourceHeight) {
      return null;
    }

    const scale = Math.min(1, MAX_CAPTURE_WIDTH / sourceWidth);
    const width = Math.round(sourceWidth * scale);
    const height = Math.round(sourceHeight * scale);
    this.captureCanvas.width = width;
    this.captureCanvas.height = height;

    const context = this.captureCanvas.getContext("2d", { alpha: false });
    context.drawImage(this.videoElement, 0, 0, width, height);
    return {
      image: this.captureCanvas.toDataURL("image/jpeg", JPEG_QUALITY),
      width,
      height,
    };
  }
}
