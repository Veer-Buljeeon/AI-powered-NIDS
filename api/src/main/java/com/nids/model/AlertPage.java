package com.nids.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.micronaut.serde.annotation.Serdeable;

import java.util.List;

/**
 * A page of alerts returned by {@code GET /alerts}, newest first. The items list
 * is always emitted (as {@code []} when empty) so the dashboard can rely on it.
 */
@Serdeable
@JsonInclude(JsonInclude.Include.ALWAYS)
public class AlertPage {

    private int page;
    private int size;
    private long total;
    private List<Alert> items;

    public AlertPage() {
    }

    public AlertPage(int page, int size, long total, List<Alert> items) {
        this.page = page;
        this.size = size;
        this.total = total;
        this.items = items;
    }

    public int getPage() {
        return page;
    }

    public void setPage(int page) {
        this.page = page;
    }

    public int getSize() {
        return size;
    }

    public void setSize(int size) {
        this.size = size;
    }

    public long getTotal() {
        return total;
    }

    public void setTotal(long total) {
        this.total = total;
    }

    public List<Alert> getItems() {
        return items;
    }

    public void setItems(List<Alert> items) {
        this.items = items;
    }
}
