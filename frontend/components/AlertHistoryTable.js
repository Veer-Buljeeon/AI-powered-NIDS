/* AlertHistoryTable - fuller tabular log of alerts (full timestamps).
   Subscribes to WebSocketClient and is seeded from GET /alerts on load. */
class AlertHistoryTable {
  constructor(tbodyEl, { pageSize = 20, keep = 200 } = {}) {
    this.tbody = tbodyEl;
    this.pageSize = pageSize;
    this.keep = keep;
    this.rows = [];
  }

  _tr(a) {
    const colour = severityColor(a.severity).dot;
    const conf = a.confidence != null ? (a.confidence * 100).toFixed(1) + "%" : "";
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${a.timestamp ? new Date(a.timestamp).toLocaleString() : ""}</td>` +
      `<td><span style="color:${colour}">●</span> ${cleanLabel(a.severity)}</td>` +
      `<td>${cleanLabel(a.classLabel)}</td>` +
      `<td>${conf}</td>` +
      `<td>${cleanLabel(a.sourceIp) || "—"}</td>` +
      `<td>${a.destinationPort == null ? "—" : a.destinationPort}</td>`;
    return tr;
  }

  add(alert) {
    this.rows.unshift(alert);
    if (this.rows.length > this.keep) this.rows.pop();
    this.render();
  }

  seed(alerts) {
    this.rows = (alerts || []).slice(0, this.keep);
    this.render();
  }

  render() {
    if (!this.rows.length) {
      this.tbody.innerHTML = '<tr><td colspan="6" class="empty">No alerts recorded.</td></tr>';
      return;
    }
    this.tbody.innerHTML = "";
    this.rows.slice(0, this.pageSize).forEach((a) => this.tbody.appendChild(this._tr(a)));
  }
}
