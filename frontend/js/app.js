/* app.js - wires the dashboard together.
   WebSocketClient is the Subject; AlertFeedRenderer, AlertHistoryTable and
   ChartManager subscribe to it. StatsPoller drives the stats-summary zone on its
   own 5s cadence. */
(function () {
  const API_BASE = "http://localhost:8080";
  const WS_URL = "ws://localhost:8080/alerts/live";

  const apiPill = document.getElementById("api-status");
  const wsPill = document.getElementById("ws-status");
  function setPill(el, ok, text) {
    el.textContent = text;
    el.className = "pill " + (ok ? "ok" : "bad");
  }

  function renderStats(payload) {
    if (!payload.ok) { setPill(apiPill, false, "API: offline"); return; }
    setPill(apiPill, true, "API: connected");
    const s = payload.stats || {};
    const sev = s.bySeverity || {};
    document.getElementById("stat-total").textContent = s.totalAlerts || 0;
    document.getElementById("stat-high").textContent = sev.HIGH || 0;
    document.getElementById("stat-medium").textContent = sev.MEDIUM || 0;
    document.getElementById("stat-benign").textContent = sev.BENIGN || 0;
    document.getElementById("stat-last").textContent =
      s.lastAlertTimestamp ? new Date(s.lastAlertTimestamp).toLocaleTimeString() : "—";
  }

  // UI components (all subscribe to the WebSocket subject)
  const feed = new AlertFeedRenderer(document.getElementById("feed"), { max: 15 });
  const history = new AlertHistoryTable(document.getElementById("history-body"), { pageSize: 20 });
  const charts = new ChartManager({
    severity: document.getElementById("chart-severity"),
    cls: document.getElementById("chart-class"),
    time: document.getElementById("chart-time"),
  });

  // Seed from the existing alert history so the view isn't empty on load.
  fetch(API_BASE + "/alerts?page=0&size=200")
    .then((r) => r.json())
    .then((p) => {
      const items = p.items || [];
      feed.seed(items);
      history.seed(items);
      charts.seed(items);
    })
    .catch(() => {});

  // Subject -> subscribers
  const ws = new WebSocketClient(WS_URL);
  ws.onStatus((ok) => setPill(wsPill, ok, ok ? "Live feed: connected" : "Live feed: disconnected"));
  ws.subscribe((alert) => { feed.add(alert); history.add(alert); charts.add(alert); });
  ws.connect();

  // Separate polling path for aggregate stats
  const poller = new StatsPoller(API_BASE, { intervalMs: 5000 });
  poller.subscribe(renderStats);
  poller.start();
})();
