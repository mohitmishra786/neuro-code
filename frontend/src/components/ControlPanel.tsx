/**
 * NeuroCode Control Panel Component
 */

import { useState } from 'react';
import { useGraphStore } from '@/stores/graphStore';

export function ControlPanel() {
    // We cannot destructure everything if we want to optimize re-renders, but for now it's fine
    // However, nodes might be updated frequently during layout.
    const nodes = useGraphStore((state) => state.nodes);
    const loadProjectTree = useGraphStore((state) => state.loadProjectTree);
    const loading = useGraphStore((state) => state.loading);

    const [path, setPath] = useState('.');

    const expandedCount = nodes.filter(n => n.data?.isExpanded).length;

    const handleLoad = () => {
        loadProjectTree(path);
    };

    return (
        <div className="control-panel">
            <div className="control-panel-stats">
                <div className="stat">
                    <span className="stat-value">{nodes.length}</span>
                    <span className="stat-label">Nodes</span>
                </div>
                <div className="stat">
                    <span className="stat-value">{expandedCount}</span>
                    <span className="stat-label">Expanded</span>
                </div>
            </div>

            <div className="control-panel-actions" style={{ display: 'flex', gap: '8px' }}>
                <input
                    type="text"
                    value={path}
                    onChange={(e) => setPath(e.target.value)}
                    placeholder="Repo Path"
                    style={{
                        background: '#333',
                        border: '1px solid #555',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        width: '200px'
                    }}
                />
                <button
                    className="control-btn"
                    onClick={handleLoad}
                    disabled={loading}
                    title="Load Repository"
                    style={{ padding: '4px 12px', fontSize: '12px' }}
                >
                    {loading ? 'Loading...' : 'Load'}
                </button>
            </div>
        </div>
    );
}

export default ControlPanel;
