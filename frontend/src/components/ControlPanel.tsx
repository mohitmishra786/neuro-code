/**
 * NeuroCode Control Panel Component
 */

import { useGraphStore } from '@/stores/graphStore';

export function ControlPanel() {
    const refresh = useGraphStore((state) => state.refresh);
    const isLoading = useGraphStore((state) => state.isLoading);
    const nodes = useGraphStore((state) => state.nodes);
    const expandedNodes = useGraphStore((state) => state.expandedNodes);

    return (
        <div className="control-panel">
            <div className="control-panel-stats">
                <div className="stat">
                    <span className="stat-value">{nodes.size}</span>
                    <span className="stat-label">Nodes</span>
                </div>
                <div className="stat">
                    <span className="stat-value">{expandedNodes.size}</span>
                    <span className="stat-label">Expanded</span>
                </div>
            </div>

            <div className="control-panel-actions">
                <button
                    className="control-btn"
                    onClick={refresh}
                    disabled={isLoading}
                    title="Refresh graph"
                >
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path
                            fillRule="evenodd"
                            d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                            clipRule="evenodd"
                        />
                    </svg>
                </button>
            </div>
        </div>
    );
}

export default ControlPanel;
