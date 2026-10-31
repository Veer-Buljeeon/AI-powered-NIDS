/* AlertFeedRenderer - the live, newest-first alert ticker (zone 4).
   Subscribes to WebSocketClient; each entry is prefixed with a plain colour-
   coded dot per the brief. Keeps the most recent `max` alerts. */
class AlertFeedRenderer {
  constructor(containerEl, { max = 15 } = {}) {
    this.el = containerEl;
    this.max = max;
    this.alerts = [];
  }

  _row(a) {
    const colour = severityColor(a.severity).dot;
    const time = a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "";
    const conf = a.confidence != null ? (a.confidence * 100).toFixed(1) + "%" : "";
    const row = document.createElement("div");
    row.className = "feed-row";
    row.innerHTML =
      `<span class="sev-dot" style="color:${colour}">●</span>` +
      `<span class="feed-sev">${cleanLabel(a.severity)}</span>` +
      `<span class="feed-class">${cleanLabel(a.classLabel)}</span>` +
      `<span class="feed-src">${cleanLabel(a.sourceIp) || "—"}:${a.destinationPort == null ? "—" : a.destinationPort}</span>` +
      `<span class="feed-conf">${conf}</span>` +
      `<span class="feed-time">${time}</span>`;
    return row;
  }

  add(alert) {
    this.alerts.unshift(alert);
    if (this.alerts.length > this.max) this.alerts.pop();
    this.render();
  }

  seed(alerts) {
    this.alerts = (alerts || []).slice(0, this.max);
    this.render();
  }

  render() {
    if (!this.alerts.length) {
      this.el.innerHTML = '<div class="empty">No alerts yet — monitoring…</div>';
      return;
    }
    this.el.innerHTML = "";
    this.alerts.forEach((a) => this.el.appendChild(this._row(a)));
  }
}
