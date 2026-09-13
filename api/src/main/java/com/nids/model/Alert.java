package com.nids.model;

import io.micronaut.serde.annotation.Serdeable;

/**
 * A persisted intrusion alert, created whenever the detection engine classifies
 * a flow as something other than BENIGN.
 */
@Serdeable
public class Alert {

    private String id;
    private String timestamp;
    private int classIndex;
    private String classLabel;
    private double confidence;
    private String severity;
    private String sourceIp;
    private Integer destinationPort;

    public Alert() {
    }

    public Alert(String id, String timestamp, int classIndex, String classLabel,
                 double confidence, String severity, String sourceIp, Integer destinationPort) {
        this.id = id;
        this.timestamp = timestamp;
        this.classIndex = classIndex;
        this.classLabel = classLabel;
        this.confidence = confidence;
        this.severity = severity;
        this.sourceIp = sourceIp;
        this.destinationPort = destinationPort;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public int getClassIndex() {
        return classIndex;
    }

    public void setClassIndex(int classIndex) {
        this.classIndex = classIndex;
    }

    public String getClassLabel() {
        return classLabel;
    }

    public void setClassLabel(String classLabel) {
        this.classLabel = classLabel;
    }

    public double getConfidence() {
        return confidence;
    }

    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public String getSourceIp() {
        return sourceIp;
    }

    public void setSourceIp(String sourceIp) {
        this.sourceIp = sourceIp;
    }

    public Integer getDestinationPort() {
        return destinationPort;
    }

    public void setDestinationPort(Integer destinationPort) {
        this.destinationPort = destinationPort;
    }
}
