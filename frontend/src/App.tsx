/**
 * NeuroCode Main App Component
 */

import { GraphCanvas } from '@/components/GraphCanvas';
import { SearchBar } from '@/components/SearchBar';
import { NodeInfoPanel } from '@/components/NodeInfoPanel';
import { Breadcrumbs } from '@/components/Breadcrumbs';
import { ControlPanel } from '@/components/ControlPanel';
import { useGraphStore } from '@/stores/graphStore';

import './App.css';

function App() {
    const error = useGraphStore((state) => state.error);

    return (
        <div className="app">
            <header className="app-header">
                <div className="app-logo">
                    <svg viewBox="0 0 32 32" fill="currentColor" className="logo-icon">
                        <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="2" fill="none" />
                        <circle cx="16" cy="10" r="3" />
                        <circle cx="10" cy="20" r="3" />
                        <circle cx="22" cy="20" r="3" />
                        <line x1="16" y1="13" x2="10" y2="17" stroke="currentColor" strokeWidth="2" />
                        <line x1="16" y1="13" x2="22" y2="17" stroke="currentColor" strokeWidth="2" />
                    </svg>
                    <h1>NeuroCode</h1>
                </div>
                <SearchBar />
                <ControlPanel />
            </header>

            <Breadcrumbs />

            {error && (
                <div className="error-banner">
                    <span>{error}</span>
                    <button onClick={() => useGraphStore.setState({ error: null })}>Dismiss</button>
                </div>
            )}

            <main className="app-main">
                <div className="graph-container">
                    <GraphCanvas />
                </div>
                <aside className="sidebar">
                    <NodeInfoPanel />
                </aside>
            </main>
        </div>
    );
}

export default App;
