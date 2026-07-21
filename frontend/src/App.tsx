/**
 * NeuroCode Main App Component
 */

import { useEffect, useState, useCallback } from 'react';
import { TreeGraph } from '@/components/TreeGraph';
import { SearchBar } from '@/components/SearchBar';
import { NodeInfoPanel } from '@/components/NodeInfoPanel';
import { Breadcrumbs } from '@/components/Breadcrumbs';
import { ControlPanel } from '@/components/ControlPanel';
import { ThemeToggle } from '@/components/ThemeToggle';
import { GraphLegend } from '@/components/GraphLegend';
import { useTreeStore } from '@/stores/treeStore';
import { useThemeStore } from '@/stores/themeStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { api } from '@/services/api';

import './App.css';

type HealthState =
    | { status: 'checking' }
    | { status: 'ok'; neo4j: string; version?: string }
    | { status: 'unreachable' }
    | { status: 'degraded'; neo4j: string; message: string };

function App() {
    const error = useTreeStore((state) => state.error);
    const mode = useThemeStore((state) => state.mode);
    const [health, setHealth] = useState<HealthState>({ status: 'checking' });

    const wsUrl =
        import.meta.env.VITE_WS_URL ||
        (import.meta.env.VITE_API_URL
            ? import.meta.env.VITE_API_URL.replace(/^http/, 'ws') + '/ws'
            : 'ws://localhost:8000/ws');

    // Live graph updates when the backend watcher notifies clients
    const { isConnected: wsConnected } = useWebSocket({ url: wsUrl });

    const checkHealth = useCallback(async () => {
        try {
            const result = await api.healthCheck();
            const neo4j = result.neo4j ?? 'unknown';
            if (neo4j === 'disconnected') {
                setHealth({
                    status: 'degraded',
                    neo4j,
                    message:
                        'API is up but Neo4j is disconnected. Start Neo4j (e.g. make up or docker compose -f docker/docker-compose.yml up -d neo4j).',
                });
            } else {
                setHealth({ status: 'ok', neo4j, version: result.version });
            }
        } catch {
            setHealth({ status: 'unreachable' });
        }
    }, []);

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', mode);
    }, [mode]);

    useEffect(() => {
        void checkHealth();
        const id = window.setInterval(() => void checkHealth(), 30000);
        return () => window.clearInterval(id);
    }, [checkHealth]);

    return (
        <div className="app">
            <header className="app-header">
                <div className="app-logo">
                    <svg viewBox="0 0 36 36" fill="none" className="logo-icon" aria-hidden>
                        <circle
                            cx="18"
                            cy="18"
                            r="16"
                            stroke="currentColor"
                            strokeWidth="2"
                            fill="none"
                            opacity="0.3"
                        />
                        <circle cx="18" cy="8" r="4" fill="currentColor" />
                        <circle cx="8" cy="24" r="4" fill="currentColor" />
                        <circle cx="28" cy="24" r="4" fill="currentColor" />
                        <circle cx="18" cy="18" r="3" fill="currentColor" opacity="0.6" />
                        <line
                            x1="18"
                            y1="12"
                            x2="18"
                            y2="15"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                        />
                        <line
                            x1="14"
                            y1="20"
                            x2="11"
                            y2="22"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                        />
                        <line
                            x1="22"
                            y1="20"
                            x2="25"
                            y2="22"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                        />
                    </svg>
                    <h1>NeuroCode</h1>
                </div>
                <SearchBar />
                <ControlPanel />
                <div
                    className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}
                    title={wsConnected ? 'Live updates connected' : 'Live updates disconnected'}
                    aria-label={wsConnected ? 'WebSocket connected' : 'WebSocket disconnected'}
                >
                    <span className="connection-dot" />
                    <span className="connection-label">{wsConnected ? 'Live' : 'Offline'}</span>
                </div>
                <ThemeToggle />
            </header>

            <Breadcrumbs />

            {health.status === 'unreachable' && (
                <div className="error-banner health-banner" role="alert">
                    <span>
                        Cannot reach the NeuroCode API at the configured URL. Start the backend
                        (port 8000) or run <code>make demo</code>.
                    </span>
                    <button type="button" onClick={() => void checkHealth()}>
                        Retry
                    </button>
                </div>
            )}

            {health.status === 'degraded' && (
                <div className="error-banner health-banner warning" role="alert">
                    <span>{health.message}</span>
                    <button type="button" onClick={() => void checkHealth()}>
                        Retry
                    </button>
                </div>
            )}

            {error && (
                <div className="error-banner" role="alert">
                    <span>{error}</span>
                    <button type="button" onClick={() => useTreeStore.setState({ error: null })}>
                        Dismiss
                    </button>
                </div>
            )}

            <main className="app-main">
                <div className="graph-container">
                    <TreeGraph />
                    <GraphLegend />
                </div>
                <aside className="sidebar">
                    <NodeInfoPanel />
                </aside>
            </main>
        </div>
    );
}

export default App;
