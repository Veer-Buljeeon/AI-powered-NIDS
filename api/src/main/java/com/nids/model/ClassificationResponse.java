package com.nids.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.micronaut.serde.annotation.Serdeable;

/**
 * Response returned by the Flask detection engine's {@code /classify} endpoint:
 * {@code {class_label, class_index, confidence}}. The snake_case JSON keys are
 * mapped onto camelCase Java fields.
 */
@Serdeable
public class ClassificationResponse {

    @JsonProperty("class_label")
    private String classLabel;

    @JsonProperty("class_index")
    private int classIndex;

    private double confidence;

    public ClassificationResponse() {
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
}
