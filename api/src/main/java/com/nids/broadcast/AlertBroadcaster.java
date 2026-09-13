package com.nids.broadcast;

import com.nids.model.Alert;
import io.micronaut.websocket.WebSocketSession;
import jakarta.inject.Singleton;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;

/**
 * Subject in the observer pattern: maintains a registry of live WebSocket
 * sessions and pushes each new alert to all of them without blocking
 * (sendAsync). Sessions register/unregister via {@code AlertSocket}.
 */
@Singleton
public class AlertBroadcaster {

    private static final Logger LOG = LoggerFactory.getLogger(AlertBroadcaster.class);

    private final Set<WebSocketSession> sessions = new CopyOnWriteArraySet<>();

    public void register(WebSocketSession session) {
        sessions.add(session);
        LOG.info("WebSocket registered: {} ({} live)", session.getId(), sessions.size());
    }

    public void unregister(WebSocketSession session) {
        sessions.remove(session);
        LOG.info("WebSocket unregistered: {} ({} live)", session.getId(), sessions.size());
    }

    public int sessionCount() {
        return sessions.size();
    }

    public void broadcast(Alert alert) {
        for (WebSocketSession session : sessions) {
            if (session.isOpen()) {
                try {
                    session.sendAsync(alert);
                } catch (Exception e) {
                    LOG.warn("Failed to push alert to {}: {}", session.getId(), e.getMessage());
                }
            }
        }
    }
}
