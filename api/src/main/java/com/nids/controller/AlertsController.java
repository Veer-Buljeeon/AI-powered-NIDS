package com.nids.controller;

import com.nids.model.AlertPage;
import com.nids.store.AlertStore;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.QueryValue;

/**
 * Paginated read access to stored alerts (newest first).
 */
@Controller("/alerts")
public class AlertsController {

    private final AlertStore alertStore;

    public AlertsController(AlertStore alertStore) {
        this.alertStore = alertStore;
    }

    @Get
    public AlertPage list(@QueryValue(defaultValue = "0") int page,
                          @QueryValue(defaultValue = "20") int size) {
        return alertStore.page(page, size);
    }
}
