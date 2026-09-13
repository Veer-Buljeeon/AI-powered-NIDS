package com.nids.store;

import com.nids.model.Alert;
import com.nids.model.AlertPage;
import jakarta.inject.Singleton;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * In-memory repository of alerts backed by a CopyOnWriteArrayList so concurrent
 * readers (controllers, stats) and the writer (the predict path) are safe
 * without explicit locking.
 */
@Singleton
public class AlertStore {

    private final CopyOnWriteArrayList<Alert> alerts = new CopyOnWriteArrayList<>();

    public void add(Alert alert) {
        alerts.add(alert);
    }

    /** Snapshot in insertion order (oldest first). */
    public List<Alert> snapshot() {
        return new ArrayList<>(alerts);
    }

    public long count() {
        return alerts.size();
    }

    /** A page of alerts, newest first. */
    public AlertPage page(int page, int size) {
        int p = Math.max(page, 0);
        int s = size <= 0 ? 20 : size;
        List<Alert> all = new ArrayList<>(alerts);
        Collections.reverse(all);
        int from = Math.min(p * s, all.size());
        int to = Math.min(from + s, all.size());
        return new AlertPage(p, s, all.size(), new ArrayList<>(all.subList(from, to)));
    }
}
