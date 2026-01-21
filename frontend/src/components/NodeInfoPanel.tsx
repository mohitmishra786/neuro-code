/**
 * NeuroCode Node Info Panel Component
 */

import { useMemo } from 'react';
import { useGraphStore } from '@/stores/graphStore';
import { NODE_COLORS } from '@/utils/colorScheme';

export function NodeInfoPanel() {
    const selectedNodeId = useGraphStore((state) => state.selectedNodeId);
    const nodes = useGraphStore((state) => state.nodes);

    const selectedNode = useMemo(() => {
        if (!selectedNodeId) return null;
        return nodes.get(selectedNodeId);
    }, [selectedNodeId, nodes]);

    if (!selectedNode) {
        return (
            <div className="node-info-panel node-info-panel-empty">
                <p>Select a node to view details</p>
            </div>
        );
    }

    return (
        <div className="node-info-panel">
            <div className="node-info-header">
                <span
                    className="node-info-type"
                    style={{ backgroundColor: NODE_COLORS[selectedNode.type]?.base || '#6b7280' }}
                >
                    {selectedNode.type}
                </span>
                <h2 className="node-info-name">{selectedNode.name}</h2>
            </div>

            {selectedNode.qualifiedName && (
                <div className="node-info-qualified">{selectedNode.qualifiedName}</div>
            )}

            <div className="node-info-stats">
                {selectedNode.lineNumber && (
                    <div className="node-info-stat">
                        <span className="stat-label">Line</span>
                        <span className="stat-value">{selectedNode.lineNumber}</span>
                    </div>
                )}
                {selectedNode.childCount > 0 && (
                    <div className="node-info-stat">
                        <span className="stat-label">Children</span>
                        <span className="stat-value">{selectedNode.childCount}</span>
                    </div>
                )}
                {selectedNode.complexity && (
                    <div className="node-info-stat">
                        <span className="stat-label">Complexity</span>
                        <span className="stat-value">{selectedNode.complexity}</span>
                    </div>
                )}
            </div>

            {selectedNode.type === 'function' && (
                <div className="node-info-function">
                    {selectedNode.isAsync && <span className="node-badge">async</span>}
                    {selectedNode.isMethod && <span className="node-badge">method</span>}
                    {selectedNode.returnType && (
                        <div className="node-info-return">
                            <span className="stat-label">Returns</span>
                            <code>{selectedNode.returnType}</code>
                        </div>
                    )}
                </div>
            )}

            {selectedNode.type === 'class' && (
                <div className="node-info-class">
                    {selectedNode.isAbstract && <span className="node-badge">abstract</span>}
                </div>
            )}

            {selectedNode.type === 'variable' && selectedNode.typeHint && (
                <div className="node-info-variable">
                    <span className="stat-label">Type</span>
                    <code>{selectedNode.typeHint}</code>
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
