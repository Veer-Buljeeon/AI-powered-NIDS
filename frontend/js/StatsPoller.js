/* StatsPoller - polls GET /stats every 5s and notifies subscribers.
   Deliberately separate from the WebSocket push path: aggregate stats don't need
   per-flow immediacy. */
class StatsPoller {
  constructor(apiBase, { intervalMs = 5000 } = {}) {
    this.url = apiBase + "/stats";
    this.intervalMs = intervalMs;
    this._subs = [];
    this._timer = null;
  }

  subscribe(callback) { this._subs.push(callback); }

  _emit(payload) {
    this._subs.forEach((cb) => { try { cb(payload); } catch (e) { console.error(e); } });
  }

  async _poll() {
    try {
      const res = await fetch(this.url);
      if (!res.ok) throw new Error("HTTP " + res.status);
      this._emit({ ok: true, stats: await res.json() });
    } catch (e) {
      this._emit({ ok: false, error: e });
    }
  }

  start() {
    this._poll();
    this._timer = setInterval(() => this._poll(), this.intervalMs);
  }

  stop() { clearInterval(this._timer); }
}
