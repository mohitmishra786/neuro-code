/**
 * useWebSocket Hook
 *
 * Manages WebSocket connection for real-time updates.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useTreeStore } from '@/stores/treeStore';

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

interface WebSocketMessage {
    type: string;
    data?: {
        file?: string;
        node_id?: string;
        changes?: Array<{
            type: 'added' | 'modified' | 'removed';
            node_id: string;
        }>;
    };
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
    const {
        url = 'ws://localhost:8000/ws',
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

    const loadRootNodes = useTreeStore((s) => s.loadRootNodes);
    const reset = useTreeStore((s) => s.reset);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const ws = new WebSocket(url);

            ws.onopen = () => {
                setState((prev) => ({ ...prev, isConnected: true, error: null }));
                reconnectCountRef.current = 0;
                console.log('[WebSocket] Connected');
            };

            ws.onmessage = (event) => {
                try {
                    const data: WebSocketMessage = JSON.parse(event.data);
                    setState((prev) => ({ ...prev, lastMessage: data }));

                    // Handle specific message types
                    switch (data.type) {
                        case 'graph_updated':
                        case 'file_changed':
                            console.log('[WebSocket] Graph update received:', data);
                            reset();
                            loadRootNodes();
                            break;
                        
                        case 'node_updated':
                            console.log('[WebSocket] Node update:', data.data?.node_id);
                            break;
                        
                        case 'connected':
                            console.log('[WebSocket] Server acknowledged connection');
                            break;
                        
                        default:
                            console.log('[WebSocket] Unknown message type:', data.type);
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
                console.log('[WebSocket] Disconnected');

                if (reconnectCountRef.current < maxReconnectAttempts) {
                    reconnectCountRef.current += 1;
                    console.log(`[WebSocket] Reconnecting (${reconnectCountRef.current}/${maxReconnectAttempts})...`);
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
    }, [url, onMessage, reconnectInterval, maxReconnectAttempts, loadRootNodes, reset]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        reconnectCountRef.current = maxReconnectAttempts;
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
