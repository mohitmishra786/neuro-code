/**
 * NeuroCode Control Panel Component
 */

import { useTreeStore } from '@/stores/treeStore';

export function ControlPanel() {
    const nodes = useTreeStore((state) => state.nodes);
    const expandedIds = useTreeStore((state) => state.expandedIds);
    const isLoading = useTreeStore((state) => state.isLoading);
    const loadRootNodes = useTreeStore((state) => state.loadRootNodes);
    const reset = useTreeStore((state) => state.reset);

    const handleRefresh = () => {
        reset();
        loadRootNodes();
    };

    return (
        <div className="control-panel">
            <div className="control-panel-stats">
                <div className="stat">
                    <span className="stat-value">{nodes.length}</span>
                    <span className="stat-label">Nodes</span>
                </div>
                <div className="stat">
                    <span className="stat-value">{expandedIds.size}</span>
                    <span className="stat-label">Expanded</span>
                </div>
            </div>

            <div className="control-panel-actions">
                <button
                    className="control-btn"
                    onClick={handleRefresh}
                    disabled={isLoading}
                    title="Refresh Graph"
                >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 16, height: 16 }}>
                        <path d="M1 4v6h6M23 20v-6h-6" />
                        <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                    </svg>
                    {isLoading ? 'Loading...' : 'Refresh'}
                </button>
            </div>
        </div>
    );
}

export default ControlPanel;
