/**
 * NeuroCode Node Info Panel Component
 */

import { useTreeStore, NODE_COLORS } from '@/stores/treeStore';

export function NodeInfoPanel() {
    const selectedNodeId = useTreeStore((state) => state.selectedNodeId);
    const getNode = useTreeStore((state) => state.getNode);
    const isExpanded = useTreeStore((state) => state.isExpanded);
    const expandNode = useTreeStore((state) => state.expandNode);
    const collapseNode = useTreeStore((state) => state.collapseNode);
    
    const selectedNode = selectedNodeId ? getNode(selectedNodeId) : null;
    const expanded = selectedNodeId ? isExpanded(selectedNodeId) : false;

    if (!selectedNode) {
        return (
            <div className="node-info-panel node-info-panel-empty">
                <div className="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 16v-4m0-4h.01" />
                    </svg>
                    <p>Select a node to view details</p>
                </div>
            </div>
        );
    }

    const color = NODE_COLORS[selectedNode.type] || NODE_COLORS.unknown;

    return (
        <div className="node-info-panel">
            <div className="node-info-header">
                <span
                    className="node-info-type"
                    style={{ backgroundColor: color }}
                >
                    {selectedNode.type}
                </span>
                <h2 className="node-info-name">{selectedNode.name}</h2>
            </div>

            {selectedNode.qualifiedName && (
                <div className="node-info-qualified">{selectedNode.qualifiedName}</div>
            )}

            <div className="node-info-stats">
                {selectedNode.childCount > 0 && (
                    <div className="node-info-stat">
                        <span className="stat-label">Children</span>
                        <span className="stat-value">{selectedNode.childCount}</span>
                    </div>
                )}
                {selectedNode.lineNumber && (
                    <div className="node-info-stat">
                        <span className="stat-label">Line</span>
                        <span className="stat-value">{selectedNode.lineNumber}</span>
                    </div>
                )}
                {selectedNode.complexity && (
                    <div className="node-info-stat">
                        <span className="stat-label">Complexity</span>
                        <span 
                            className="stat-value"
                            style={{ 
                                color: selectedNode.complexity > 10 ? '#ef4444' : 
                                       selectedNode.complexity > 5 ? '#f59e0b' : 'inherit' 
                            }}
                        >
                            {selectedNode.complexity}
                        </span>
                    </div>
                )}
                {selectedNode.isAsync && (
                    <div className="node-info-badge">
                        <span>⚡ Async</span>
                    </div>
                )}
            </div>

            {selectedNode.childCount > 0 && (
                <div className="node-info-actions">
                    <button
                        className="node-info-action"
                        onClick={() => expanded ? collapseNode(selectedNode.id) : expandNode(selectedNode.id)}
                    >
                        {expanded ? (
                            <>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M5 12h14" />
                                </svg>
                                Collapse
                            </>
                        ) : (
                            <>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M12 5v14m-7-7h14" />
                                </svg>
                                Expand
                            </>
                        )}
                    </button>
                </div>
            )}

            {selectedNode.docstring && (
                <div className="node-info-docstring">
                    <h3>Documentation</h3>
                    <p>{selectedNode.docstring}</p>
                </div>
            )}
        </div>
    );
}

export default NodeInfoPanel;
