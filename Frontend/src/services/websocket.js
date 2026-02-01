// WebSocket Service for Real-time Updates
const WS_URL = 'ws://localhost:8000/ws/dashboard';

class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 5000;
        this.reconnectTimer = null;
        this.eventCallbacks = new Map();
        this.isConnecting = false;
    }

    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }

        this.isConnecting = true;
        console.log('[WebSocket] Connecting to', WS_URL);

        try {
            this.ws = new WebSocket(WS_URL);

            this.ws.onopen = () => {
                console.log('[WebSocket] ✅ Connected to AtherOps backend');
                this.isConnecting = false;
                if (this.reconnectTimer) {
                    clearTimeout(this.reconnectTimer);
                    this.reconnectTimer = null;
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[WebSocket] Received:', data.type);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('[WebSocket] Error parsing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[WebSocket] ❌ Error:', error);
                this.isConnecting = false;
            };

            this.ws.onclose = () => {
                console.log('[WebSocket] Connection closed, reconnecting...');
                this.isConnecting = false;
                this.scheduleReconnect();
            };
        } catch (error) {
            console.error('[WebSocket] Failed to connect:', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (!this.reconnectTimer) {
            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                this.connect();
            }, this.reconnectInterval);
        }
    }

    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    handleMessage(data) {
        const { type } = data;

        // Call registered callbacks for this event type
        const callbacks = this.eventCallbacks.get(type) || [];
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`[WebSocket] Error in callback for ${type}:`, error);
            }
        });

        // Also call wildcard callbacks
        const wildcardCallbacks = this.eventCallbacks.get('*') || [];
        wildcardCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('[WebSocket] Error in wildcard callback:', error);
            }
        });
    }

    // Register a callback for a specific event type
    on(eventType, callback) {
        if (!this.eventCallbacks.has(eventType)) {
            this.eventCallbacks.set(eventType, []);
        }
        this.eventCallbacks.get(eventType).push(callback);
    }

    // Remove a callback
    off(eventType, callback) {
        const callbacks = this.eventCallbacks.get(eventType);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    // Send a message to the backend
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('[WebSocket] Cannot send message, not connected');
        }
    }

    // Approve an action plan
    approveAction(planId) {
        this.send({
            action: 'approve',
            plan_id: planId,
        });
    }
}

export default new WebSocketService();
