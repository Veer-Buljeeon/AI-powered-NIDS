package com.nids.client;

import com.nids.model.ClassificationResponse;
import com.nids.model.ClassifyRequest;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.annotation.Client;

/**
 * Adapter around the Python Flask detection engine (Phase 3). Declarative HTTP
 * client bound to the named "detection" service, whose base URL is configured
 * by {@code micronaut.http.services.detection.url} (backed by the
 * DETECTION_ENGINE_URL environment variable) and is never hardcoded, so the
 * engine can be relocated without code changes.
 */
@Client(id = "detection")
public interface DetectionClient {

    @Post("/classify")
    ClassificationResponse classify(@Body ClassifyRequest request);
}
