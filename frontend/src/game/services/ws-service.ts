interface WebSocketMessage {
    action: string;
    data: unknown;
};

export interface WebSocketService {
    connect: () => void;
    send: <T extends WebSocketMessage>(message: T) => void;
    subscribe: <T extends WebSocketMessage>(action: string, callback: (message: T) => void) => void;
    disconnect: () => void;
};

export function createWebSocketService(): WebSocketService {
    let ws: WebSocket | null = null;
    const listeners = new Map<string, Set<(message: any) => void>>();
    
    return {
        connect: () => {
            if (ws) return;

            ws = new WebSocket("ws://localhost:8000");

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data) as WebSocketMessage;

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
            listeners.get(action)?.add(callback);
        },
        disconnect: () => {
            
        },
    };
}