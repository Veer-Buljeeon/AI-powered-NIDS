package com.nids.websocket;

import com.nids.broadcast.AlertBroadcaster;
import io.micronaut.websocket.WebSocketSession;
import io.micronaut.websocket.annotation.OnClose;
import io.micronaut.websocket.annotation.OnMessage;
import io.micronaut.websocket.annotation.OnOpen;
import io.micronaut.websocket.annotation.ServerWebSocket;

/**
 * WebSocket endpoint clients connect to for the live alert feed. The feed is
 * one-way (server -> client): inbound messages are ignored. Session lifecycle
 * is delegated to the {@link AlertBroadcaster} registry.
 */
@ServerWebSocket("/alerts/live")
public class AlertSocket {

    private final AlertBroadcaster broadcaster;

    public AlertSocket(AlertBroadcaster broadcaster) {
        this.broadcaster = broadcaster;
    }

    @OnOpen
    public void onOpen(WebSocketSession session) {
        broadcaster.register(session);
    }

    @OnMessage
    public void onMessage(String message, WebSocketSession session) {
        // Listen-only feed; ignore anything a client sends.
    }

    @OnClose
    public void onClose(WebSocketSession session) {
        broadcaster.unregister(session);
    }
}
