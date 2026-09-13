package com.nids.controller;

import com.nids.broadcast.AlertBroadcaster;
import com.nids.client.DetectionClient;
import com.nids.model.Alert;
import com.nids.model.ClassificationResponse;
import com.nids.model.ClassifyRequest;
import com.nids.model.FlowRequest;
import com.nids.model.PredictResult;
import com.nids.service.SeverityClassifier;
import com.nids.store.AlertStore;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Post;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * Orchestrates a prediction: forwards the flow's feature vector to the detection
 * engine and, when the result is malicious, records and broadcasts an alert.
 * Holds no detection logic of its own. Runs on the blocking executor because it
 * makes a synchronous downstream HTTP call.
 */
@Controller("/predict")
public class PredictController {

    private static final Logger LOG = LoggerFactory.getLogger(PredictController.class);

    private final DetectionClient detectionClient;
    private final AlertStore alertStore;
    private final AlertBroadcaster broadcaster;
    private final SeverityClassifier severityClassifier;

    public PredictController(DetectionClient detectionClient,
                            AlertStore alertStore,
                            AlertBroadcaster broadcaster,
                            SeverityClassifier severityClassifier) {
        this.detectionClient = detectionClient;
        this.alertStore = alertStore;
        this.broadcaster = broadcaster;
        this.severityClassifier = severityClassifier;
    }

    @Post
    @ExecuteOn(TaskExecutors.BLOCKING)
    public HttpResponse<?> predict(@Body FlowRequest request) {
        if (request == null || request.getFeatures() == null || request.getFeatures().isEmpty()) {
            return HttpResponse.badRequest(Map.of("error", "'features' must be a non-empty array"));
        }

        ClassificationResponse classification;
        try {
            classification = detectionClient.classify(new ClassifyRequest(request.getFeatures()));
        } catch (Exception e) {
            LOG.error("Detection engine call failed: {}", e.getMessage());
            return HttpResponse.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of(
                            "error", "Detection engine unavailable",
                            "detail", String.valueOf(e.getMessage())));
        }

        String label = classification.getClassLabel();
        boolean malicious = severityClassifier.isMalicious(label);
        String severity = severityClassifier.severityFor(label);
        String alertId = null;

        if (malicious) {
            Alert alert = new Alert(
                    UUID.randomUUID().toString(),
                    Instant.now().toString(),
                    classification.getClassIndex(),
                    label,
                    classification.getConfidence(),
                    severity,
                    request.getSourceIp(),
                    request.getDestinationPort());
            alertStore.add(alert);
            broadcaster.broadcast(alert);
            alertId = alert.getId();
            LOG.info("ALERT [{}] {} (confidence {})", severity, label, classification.getConfidence());
        }

        return HttpResponse.ok(new PredictResult(
                label, classification.getClassIndex(), classification.getConfidence(),
                malicious, severity, alertId));
    }
}
