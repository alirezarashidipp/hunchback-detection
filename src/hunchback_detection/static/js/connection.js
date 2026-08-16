export class AnalysisConnection {
  constructor({ onAnalysis, onError, onStateChange }) {
    this.onAnalysis = onAnalysis;
    this.onError = onError;
    this.onStateChange = onStateChange;
    this.socket = null;
    this.frameInFlight = false;
  }

  connect() {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      this.socket = new WebSocket(`${protocol}//${window.location.host}/ws/analyze`);
      this.onStateChange("connecting");

      this.socket.addEventListener("open", () => {
        this.onStateChange("connected");
        resolve();
      }, { once: true });

      this.socket.addEventListener("message", (event) => {
        this.frameInFlight = false;
        let message;
        try {
          message = JSON.parse(event.data);
        } catch {
          this.onError("The analysis service returned an unreadable message.");
          return;
        }

        if (message.type === "analysis") {
          this.onAnalysis(message);
          return;
        }
        this.onError(message.message || "The frame could not be analyzed.");
      });

      this.socket.addEventListener("error", () => {
        this.frameInFlight = false;
        reject(new Error("Could not connect to the local analysis service."));
      }, { once: true });

      this.socket.addEventListener("close", () => {
        this.frameInFlight = false;
        this.onStateChange("disconnected");
      });
    });
  }

  sendFrame(image, threshold) {
    if (this.socket?.readyState !== WebSocket.OPEN || this.frameInFlight) {
      return false;
    }
    this.frameInFlight = true;
    this.socket.send(JSON.stringify({ type: "frame", image, threshold }));
    return true;
  }

  close() {
    this.frameInFlight = false;
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.close(1000, "camera stopped");
    }
    this.socket = null;
  }
}
