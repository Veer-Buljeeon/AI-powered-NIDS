/* ChartManager - Facade over three Chart.js instances:
     1. alerts by severity (doughnut)
     2. alerts by class    (horizontal bar)
     3. alerts over time    (line, per-minute)
   Subscribes to WebSocketClient; counts are accumulated from the alert stream
   (seeded from GET /alerts on load). Callers never touch Chart.js directly. */
class ChartManager {
  constructor(ctx) {
    this.sev = {};               // severity -> count
    this.cls = {};               // class label -> count
    this.buckets = new Map();    // minute label -> count
    this.maxBuckets = 15;

    const tick = "#8b97a7";
    this.severityChart = new Chart(ctx.severity, {
      type: "doughnut",
      data: { labels: [], datasets: [{ data: [], backgroundColor: [], borderWidth: 0 }] },
      options: { responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: "bottom", labels: { color: tick } } } },
    });
    this.classChart = new Chart(ctx.cls, {
      type: "bar",
      data: { labels: [], datasets: [{ label: "Alerts", data: [], backgroundColor: "#3b82f6", borderRadius: 4 }] },
      options: { indexAxis: "y", responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, ticks: { color: tick, precision: 0 }, grid: { color: "rgba(137,135,129,.15)" } },
                  y: { ticks: { color: tick }, grid: { display: false } } } },
    });
    this.timeChart = new Chart(ctx.time, {
      type: "line",
      data: { labels: [], datasets: [{ label: "Alerts/min", data: [], borderColor: "#3b82f6",
        backgroundColor: "rgba(59,130,246,.15)", fill: true, tension: 0.3, pointRadius: 2 }] },
      options: { responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { ticks: { color: tick }, grid: { display: false } },
                  y: { beginAtZero: true, ticks: { color: tick, precision: 0 }, grid: { color: "rgba(137,135,129,.15)" } } } },
    });
  }

  _bucketLabel(ts) {
    const d = ts ? new Date(ts) : new Date();
    d.setSeconds(0, 0);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  _ingest(a) {
    const sev = (cleanLabel(a.severity) || "UNKNOWN").toUpperCase();
    this.sev[sev] = (this.sev[sev] || 0) + 1;
    const cls = cleanLabel(a.classLabel) || "unknown";
    this.cls[cls] = (this.cls[cls] || 0) + 1;
    const b = this._bucketLabel(a.timestamp);
    this.buckets.set(b, (this.buckets.get(b) || 0) + 1);
    while (this.buckets.size > this.maxBuckets) {
      this.buckets.delete(this.buckets.keys().next().value);
    }
  }

  add(alert) { this._ingest(alert); this.render(); }

  seed(alerts) {
    (alerts || []).slice().reverse().forEach((a) => this._ingest(a));  // oldest first
    this.render();
  }

  render() {
    const sevKeys = Object.keys(this.sev);
    this.severityChart.data.labels = sevKeys;
    this.severityChart.data.datasets[0].data = sevKeys.map((k) => this.sev[k]);
    this.severityChart.data.datasets[0].backgroundColor = sevKeys.map((k) => severityColor(k).dot);
    this.severityChart.update();

    const clsEntries = Object.entries(this.cls).sort((a, b) => b[1] - a[1]);
    this.classChart.data.labels = clsEntries.map((e) => e[0]);
    this.classChart.data.datasets[0].data = clsEntries.map((e) => e[1]);
    this.classChart.update();

    this.timeChart.data.labels = [...this.buckets.keys()];
    this.timeChart.data.datasets[0].data = [...this.buckets.values()];
    this.timeChart.update();
  }
}
