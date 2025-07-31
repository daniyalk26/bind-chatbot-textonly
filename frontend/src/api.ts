import axios from 'axios';

/* ───────────── Base URL helpers ───────────── */

// ①  Read the value that Vite injects at build time
const ENV_BASE = import.meta.env.VITE_API_URL as string | undefined;

/* ②  Fallbacks for running the frontend any way you like
      – inside Docker (`ENV_BASE` will exist) or
      – directly on your laptop (`localhost:8000`). */
export const API_BASE_URL =
  ENV_BASE ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

/* ③  Axios instance */
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

/* ───────────── WebSocket helper ───────────── */

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectInterval = 5_000; // 5 s
  private shouldReconnect = true;
  private sessionId: string;

  constructor(
    private onMessage: (data: unknown) => void,
    private onConnect: () => void,
    private onDisconnect: () => void
  ) {
    this.sessionId = this.getOrCreateSessionId();
  }

  /* -------- private -------- */
  private getOrCreateSessionId(): string {
    let sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random()
        .toString(36)
        .slice(2, 11)}`;
      localStorage.setItem('session_id', sessionId);
    }
    return sessionId;
  }

  /* -------- public -------- */
  connect() {
    // http  → ws     |  https → wss
    const wsScheme = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
    const wsUrl = `${wsScheme}://${wsHost}/ws?session=${this.sessionId}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('[WebSocket] connected');
      this.onConnect();
    };

    this.ws.onmessage = (event) => {
      try {
        this.onMessage(JSON.parse(event.data));
      } catch (err) {
        console.error('[WebSocket] JSON parse error:', err);
      }
    };

    this.ws.onclose = () => {
      console.log('[WebSocket] disconnected');
      this.onDisconnect();
      if (this.shouldReconnect)
        setTimeout(() => this.connect(), this.reconnectInterval);
    };

    this.ws.onerror = (err) => console.error('[WebSocket] error:', err);
  }

  send(payload: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    this.ws?.close();
  }
}

export { WebSocketClient };
export default WebSocketClient;
