/* WebSocketClient - Subject in the observer pattern.
   Connects to the API's /alerts/live stream, lets components subscribe to new
   alerts (and to connection-status changes), and auto-reconnects 5s after a
   disconnect. */
class WebSocketClient {
  constructor(url, { reconnectMs = 5000 } = {}) {
    this.url = url;
    this.reconnectMs = reconnectMs;
    this._alertSubs = [];
    this._statusSubs = [];
    this.ws = null;
  }

  subscribe(callback) { this._alertSubs.push(callback); }
  onStatus(callback) { this._statusSubs.push(callback); }

  _emitAlert(alert) {
    this._alertSubs.forEach((cb) => { try { cb(alert); } catch (e) { console.error(e); } });
  }
  _emitStatus(connected) {
    this._statusSubs.forEach((cb) => { try { cb(connected); } catch (e) { console.error(e); } });
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => this._emitStatus(true);
      this.ws.onmessage = (ev) => {
        try { this._emitAlert(JSON.parse(ev.data)); }
        catch (e) { console.error("bad alert payload", e); }
      };
      this.ws.onclose = () => {
        this._emitStatus(false);
        setTimeout(() => this.connect(), this.reconnectMs);
      };
      this.ws.onerror = () => { try { this.ws.close(); } catch (_) {} };
    } catch (e) {
      this._emitStatus(false);
      setTimeout(() => this.connect(), this.reconnectMs);
    }
  }
}
