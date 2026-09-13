package com.nids.service;

import jakarta.inject.Singleton;

/**
 * Maps a model class label to an alert severity band and decides whether a label
 * counts as malicious. Severity bands align with the Phase 5 dashboard colours:
 * HIGH (red) for denial-of-service and brute-force/web attacks, MEDIUM (amber)
 * for reconnaissance/suspicious activity, BENIGN (green) for normal traffic.
 */
@Singleton
public class SeverityClassifier {

    public boolean isMalicious(String label) {
        return label != null && !label.equalsIgnoreCase("BENIGN");
    }

    public String severityFor(String label) {
        if (label == null) {
            return "UNKNOWN";
        }
        String l = label.toLowerCase();
        if (l.equals("benign")) {
            return "BENIGN";
        }
        if (l.contains("portscan") || l.contains("port scan")
                || l.contains("infiltration") || l.contains("bot")) {
            return "MEDIUM";
        }
        return "HIGH";
    }
}
