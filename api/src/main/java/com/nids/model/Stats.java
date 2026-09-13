package com.nids.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.micronaut.serde.annotation.Serdeable;

import java.util.Map;

/**
 * Aggregate statistics returned by {@code GET /stats}, computed on demand from
 * the current contents of the alert store. Empty maps are always emitted so the
 * dashboard can rely on a stable shape.
 */
@Serdeable
@JsonInclude(JsonInclude.Include.ALWAYS)
public class Stats {

    private long totalAlerts;
    private Map<String, Long> byClass;
    private Map<String, Long> bySeverity;
    private String lastAlertTimestamp;

    public Stats() {
    }

    public Stats(long totalAlerts, Map<String, Long> byClass,
                 Map<String, Long> bySeverity, String lastAlertTimestamp) {
        this.totalAlerts = totalAlerts;
        this.byClass = byClass;
        this.bySeverity = bySeverity;
        this.lastAlertTimestamp = lastAlertTimestamp;
    }

    public long getTotalAlerts() {
        return totalAlerts;
    }

    public void setTotalAlerts(long totalAlerts) {
        this.totalAlerts = totalAlerts;
    }

    public Map<String, Long> getByClass() {
        return byClass;
    }

    public void setByClass(Map<String, Long> byClass) {
        this.byClass = byClass;
    }

    public Map<String, Long> getBySeverity() {
        return bySeverity;
    }

    public void setBySeverity(Map<String, Long> bySeverity) {
        this.bySeverity = bySeverity;
    }

    public String getLastAlertTimestamp() {
        return lastAlertTimestamp;
    }

    public void setLastAlertTimestamp(String lastAlertTimestamp) {
        this.lastAlertTimestamp = lastAlertTimestamp;
    }
}
