package com.nids.controller;

import com.nids.model.Alert;
import com.nids.model.Stats;
import com.nids.store.AlertStore;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Aggregate statistics computed on demand from the alert store (never a
 * separately maintained counter, so the numbers cannot drift).
 */
@Controller("/stats")
public class StatsController {

    private final AlertStore alertStore;

    public StatsController(AlertStore alertStore) {
        this.alertStore = alertStore;
    }

    @Get
    public Stats stats() {
        List<Alert> all = alertStore.snapshot();
        Map<String, Long> byClass = new LinkedHashMap<>();
        Map<String, Long> bySeverity = new LinkedHashMap<>();
        for (Alert a : all) {
            byClass.merge(a.getClassLabel(), 1L, Long::sum);
            bySeverity.merge(a.getSeverity(), 1L, Long::sum);
        }
        String last = all.isEmpty() ? null : all.get(all.size() - 1).getTimestamp();
        return new Stats(all.size(), byClass, bySeverity, last);
    }
}
