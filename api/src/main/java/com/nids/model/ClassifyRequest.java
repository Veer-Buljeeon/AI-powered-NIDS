package com.nids.model;

import io.micronaut.serde.annotation.Serdeable;

import java.util.List;

/**
 * Body sent to the Flask detection engine's {@code POST /classify} endpoint.
 * Only the feature vector crosses this boundary.
 */
@Serdeable
public class ClassifyRequest {

    private List<Double> features;

    public ClassifyRequest() {
    }

    public ClassifyRequest(List<Double> features) {
        this.features = features;
    }

    public List<Double> getFeatures() {
        return features;
    }

    public void setFeatures(List<Double> features) {
        this.features = features;
    }
}
