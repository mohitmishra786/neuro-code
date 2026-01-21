/**
 * NeuroCode Main App Component
 */

import { useEffect } from 'react';
import { GraphCanvas } from '@/components/GraphCanvas';
import { SearchBar } from '@/components/SearchBar';
import { NodeInfoPanel } from '@/components/NodeInfoPanel';
import { Breadcrumbs } from '@/components/Breadcrumbs';
import { ControlPanel } from '@/components/ControlPanel';
import { ThemeToggle } from '@/components/ThemeToggle';
import { useGraphStore } from '@/stores/graphStore';
import { useThemeStore } from '@/stores/themeStore';

import './App.css';

function App() {
    const error = useGraphStore((state) => state.error);
    const mode = useThemeStore((state) => state.mode);

    // Apply theme on mount
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', mode);
    }, [mode]);

    return (
        <div className="app">
            <header className="app-header">
                <div className="app-logo">
                    <svg viewBox="0 0 36 36" fill="none" className="logo-icon">
                        <circle cx="18" cy="18" r="16" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.3" />
                        <circle cx="18" cy="8" r="4" fill="currentColor" />
                        <circle cx="8" cy="24" r="4" fill="currentColor" />
                        <circle cx="28" cy="24" r="4" fill="currentColor" />
                        <circle cx="18" cy="18" r="3" fill="currentColor" opacity="0.6" />
                        <line x1="18" y1="12" x2="18" y2="15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        <line x1="14" y1="20" x2="11" y2="22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        <line x1="22" y1="20" x2="25" y2="22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                    <h1>NeuroCode</h1>
                </div>
                <SearchBar />
                <ControlPanel />
                <ThemeToggle />
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
