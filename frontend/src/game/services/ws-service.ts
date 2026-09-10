// REACT
import { useSyncExternalStore } from 'react';

//TYPES
import type { AnyMessage, SendMessage } from "@/game/services/ws-messages";

export interface WebSocketService {
    connect: (ticket: string|null) => void;
    send: <K extends SendMessage>(message: K) => void;
    subscribe: <K extends AnyMessage["action"]>(action: K, callback: (message: Extract<AnyMessage, { action: K }>) => void) => void;
    subscribeStatus: (cb: () => void) => () => void;
    getStatus: () => ConnectionStatus;
    disconnect: () => void;
};
type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

export function createWebSocketService(): WebSocketService {
    let ws: WebSocket | null = null;
    let status: ConnectionStatus = "connecting";

    const listeners = new Map<string, Set<(message: AnyMessage) => void>>();
    const statusListeners = new Set<() => void>();
    
    const setStatus = (newStatus: ConnectionStatus) => {
        if(status === newStatus) return;
        status = newStatus;
        statusListeners.forEach((cb) => cb());
    };

    return {
        connect: (ticket?: string) => {
            if (ws) return;
            
            if (ticket){
                ws = new WebSocket(import.meta.env.VITE_WS_URL + `?one-time=${ticket}`);
            } else {
                ws = new WebSocket(import.meta.env.VITE_WS_URL);
            }

            if (ws.readyState === WebSocket.OPEN){
                setStatus("connected");
            } else if (ws.readyState === WebSocket.CLOSED){
                setStatus("disconnected");
            } else if (ws.readyState === WebSocket.CONNECTING){
                setStatus("connecting");
            } else {
                setStatus("error");
            }

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);

                    if (!message.action) return;
                    listeners.get(message.action)?.forEach((cb) => cb(message));
                } catch (err) {
                    console.error("Failed to parse WebSocket message:", err);
                }
            };

            ws.onopen = () => setStatus("connected");
            ws.onclose = () => setStatus("disconnected");
            ws.onerror = () => setStatus("error");
        },
        send: (message) => {
            if (ws) {
                ws.send(JSON.stringify(message));
            }
        },
        subscribe: (action, callback) => {
            if (!listeners.get(action)) listeners.set(action, new Set());
            listeners.get(action)?.add(callback as (message: AnyMessage) => void);
        },
        subscribeStatus: (cb) => {
            if (!statusListeners.has(cb)) statusListeners.add(cb);
            return () => { statusListeners.delete(cb); };
        },
        getStatus: () => status,
        disconnect: () => {
            if (ws){
                ws.onclose = null;
                ws.onmessage = null;
                ws.onopen = null;
                ws.onerror = null;
                ws.close();
                ws = null;
            }
            setStatus("disconnected");
        },
    };
}

export function useWebSocketStatus(ws: WebSocketService) {
    return useSyncExternalStore(ws.subscribeStatus, ws.getStatus);
}