//TYPES
import type { AnyMessage, SendMessage } from "@/game/services/ws-messages";

export interface WebSocketService {
    connect: () => void;
    send: <K extends SendMessage>(message: K) => void;
    subscribe: <K extends AnyMessage["action"]>(action: K, callback: (message: Extract<AnyMessage, { action: K }>) => void) => void;
    disconnect: () => void;
};

export function createWebSocketService(): WebSocketService {
    let ws: WebSocket | null = null;
    const listeners = new Map<string, Set<(message: AnyMessage) => void>>();
    
    return {
        connect: () => {
            if (ws) return;

            ws = new WebSocket(import.meta.env.VITE_WS_URL);

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);

                    if (!message.action) return;
                    listeners.get(message.action)?.forEach((cb) => cb(message));
                } catch (err) {
                    console.error("Failed to parse WebSocket message:", err);
                }
            };

            ws.onopen = () => console.log("WebSocket connected");
            ws.onclose = () => console.log("WebSocket disconnected");
            ws.onerror = (err) => console.error("WebSocket error:", err);
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
        disconnect: () => {
            
        },
    };
}