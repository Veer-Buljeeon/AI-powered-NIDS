/* Severity palette, shared by the feed, history table and charts.
   Colours per the project brief: red = DoS/DDoS/Brute Force (HIGH),
   amber = Port Scan/recon (MEDIUM), green = benign. Each has a bright
   variant (used for the dot/accent) and a dark variant. */
const SEVERITY_COLORS = {
  HIGH:   { dot: "#DC2626", dark: "#843C0C" },
  MEDIUM: { dot: "#D97706", dark: "#7B5E00" },
  BENIGN: { dot: "#16A34A", dark: "#217346" },
  LOW:    { dot: "#16A34A", dark: "#217346" },
};

function severityColor(severity) {
  return SEVERITY_COLORS[String(severity || "").toUpperCase()]
      || { dot: "#8b97a7", dark: "#5f5e5a" };
}

/* The three CICIDS2017 'Web Attack' labels carry a non-ASCII artefact from the
   raw CSVs; clean it for display. */
function cleanLabel(s) {
  return String(s == null ? "" : s)
      .replace(/�|ï¿½|\u0096/g, "-")
      .replace(/\s+/g, " ")
      .trim();
}
