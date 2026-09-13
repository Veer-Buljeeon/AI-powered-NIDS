package com.nids.model;

import io.micronaut.serde.annotation.Serdeable;

/**
 * Response returned by {@code POST /predict}: the classification plus whether it
 * was treated as malicious and, if so, the id of the alert that was raised.
 */
@Serdeable
public class PredictResult {

    private String classLabel;
    private int classIndex;
    private double confidence;
    private boolean malicious;
    private String severity;
    private String alertId;

    public PredictResult() {
    }

    public PredictResult(String classLabel, int classIndex, double confidence,
                         boolean malicious, String severity, String alertId) {
        this.classLabel = classLabel;
        this.classIndex = classIndex;
        this.confidence = confidence;
        this.malicious = malicious;
        this.severity = severity;
        this.alertId = alertId;
    }

    public String getClassLabel() {
        return classLabel;
    }

    public void setClassLabel(String classLabel) {
        this.classLabel = classLabel;
    }

    public int getClassIndex() {
        return classIndex;
    }

    public void setClassIndex(int classIndex) {
        this.classIndex = classIndex;
    }

    public double getConfidence() {
        return confidence;
    }

    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }

    public boolean isMalicious() {
        return malicious;
    }

    public void setMalicious(boolean malicious) {
        this.malicious = malicious;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public String getAlertId() {
        return alertId;
    }

    public void setAlertId(String alertId) {
        this.alertId = alertId;
    }
}
