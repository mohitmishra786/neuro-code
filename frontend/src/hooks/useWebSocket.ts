/**
 * useWebSocket Hook
 *
 * Manages WebSocket connection for real-time updates.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useGraphStore } from '@/stores/graphStore';

type MessageHandler = (data: unknown) => void;

interface UseWebSocketOptions {
    url?: string;
    onMessage?: MessageHandler;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

interface WebSocketState {
    isConnected: boolean;
    lastMessage: unknown | null;
    error: string | null;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
    const {
        url = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
        onMessage,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5,
    } = options;

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectCountRef = useRef(0);
    const reconnectTimeoutRef = useRef<number | null>(null);

    const [state, setState] = useState<WebSocketState>({
        isConnected: false,
        lastMessage: null,
        error: null,
    });

    const refresh = useGraphStore((s) => s.refresh);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const ws = new WebSocket(url);

            ws.onopen = () => {
                setState((prev) => ({ ...prev, isConnected: true, error: null }));
                reconnectCountRef.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setState((prev) => ({ ...prev, lastMessage: data }));

                    // Handle specific message types
                    if (data.type === 'graph_updated') {
                        refresh();
                    }

                    onMessage?.(data);
                } catch {
                    // Non-JSON message, ignore
                }
            };

            ws.onerror = () => {
                setState((prev) => ({ ...prev, error: 'WebSocket error' }));
            };

            ws.onclose = () => {
                setState((prev) => ({ ...prev, isConnected: false }));
                wsRef.current = null;

                // Attempt reconnection
                if (reconnectCountRef.current < maxReconnectAttempts) {
                    reconnectCountRef.current += 1;
                    reconnectTimeoutRef.current = window.setTimeout(connect, reconnectInterval);
                }
            };

            wsRef.current = ws;
        } catch (error) {
            setState((prev) => ({
                ...prev,
                error: error instanceof Error ? error.message : 'Connection failed',
            }));
        }
    }, [url, onMessage, reconnectInterval, maxReconnectAttempts, refresh]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        reconnectCountRef.current = maxReconnectAttempts; // Prevent auto-reconnect
        wsRef.current?.close();
        wsRef.current = null;
        setState((prev) => ({ ...prev, isConnected: false }));
    }, [maxReconnectAttempts]);

    const send = useCallback((data: unknown) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        }
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        ...state,
        connect,
        disconnect,
        send,
    };
}

export default useWebSocket;
