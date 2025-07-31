import axios from 'axios';

/* ───────────── Base URL helpers ───────────── */
const ENV_BASE = import.meta.env.VITE_API_URL as string | undefined;
export const API_BASE_URL =
  ENV_BASE || `${window.location.protocol}//${window.location.hostname}:8000`;

/* ③  Axios instance — still handy for REST calls */
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

/* ───────────── WebSocket helper ───────────── */
class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectInterval = 5_000;
  private shouldReconnect = true;
  private sessionId: string;

  constructor(
    private onMessage: (data: any) => void,
    private onConnect: () => void,
    private onDisconnect: () => void
  ) {
    this.sessionId = this.getOrCreateSessionId();
  }

  /* -------- utils -------- */
  private getOrCreateSessionId() {
    let id = localStorage.getItem('session_id');
    if (!id) {
      id = `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
      localStorage.setItem('session_id', id);
    }
    return id;
  }

  /* -------- public -------- */
  connect() {
    const wsScheme = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const wsHost   = API_BASE_URL.replace(/^https?:\/\//, '');
    const url      = `${wsScheme}://${wsHost}/ws?session=${this.sessionId}`;

    this.ws = new WebSocket(url);

    this.ws.onopen    = () => { console.log('[WS] open');  this.onConnect(); };
    this.ws.onclose   = () => { console.log('[WS] close'); this.onDisconnect();
                                if (this.shouldReconnect) setTimeout(()=>this.connect(),this.reconnectInterval); };
    this.ws.onerror   = (e) =>  console.error('[WS] error:', e);
    this.ws.onmessage = (e) => {
      try   { this.onMessage(JSON.parse(e.data)); }
      catch { console.error('[WS] bad JSON', e.data); }
    };
  }

  /** generic JSON payload */
  send(payload: any) {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(payload));
  }

  /** helper for audio -> base64 (future voice feature) */
  sendAudio(buf: ArrayBuffer) {
    const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
    this.send({ type: 'user_audio', content: b64 });
  }

  disconnect() { this.shouldReconnect = false; this.ws?.close(); }
}

export { WebSocketClient };
export default WebSocketClient;
