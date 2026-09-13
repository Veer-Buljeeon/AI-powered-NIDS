package com.nids.model;

import io.micronaut.serde.annotation.Serdeable;

import java.util.List;

/**
 * Incoming request to {@code POST /predict}: a single network-flow feature
 * vector plus optional metadata used to enrich the resulting alert.
 */
@Serdeable
public class FlowRequest {

    private List<Double> features;
    private String sourceIp;
    private Integer destinationPort;

    public FlowRequest() {
    }

    public List<Double> getFeatures() {
        return features;
    }

    public void setFeatures(List<Double> features) {
        this.features = features;
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
