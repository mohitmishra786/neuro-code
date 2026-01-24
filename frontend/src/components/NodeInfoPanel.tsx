/**
 * NeuroCode Node Info Panel Component
 */

import { useMemo } from 'react';
import { useGraphStore } from '@/stores/graphStore';
import { NODE_COLORS } from '@/utils/colorScheme';

export function NodeInfoPanel() {
    const nodes = useGraphStore((state) => state.nodes);

    const selectedNode = useMemo(() => {
        const node = nodes.find((n) => n.selected);
        if (!node) return null;
        // Map React Flow node data back to a structure NodeInfoPanel can use
        // The original ProjectTreeNode is in node.data.original
        const original = node.data?.original;
        if (!original) return null;

        return {
            name: original.label || original.id,
            type: original.type,
            qualifiedName: original.data?.qualified_name,
            lineNumber: original.data?.line_number, // might differ based on tree_builder
            childCount: original.children?.length || 0,
            complexity: original.data?.complexity,
            docstring: original.data?.docstring,
            isAsync: original.data?.is_async,
            returnType: original.data?.return_type,
            typeHint: original.data?.type_hint,
        };
    }, [nodes]);

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
                {selectedNode.childCount > 0 && (
                    <div className="node-info-stat">
                        <span className="stat-label">Children</span>
                        <span className="stat-value">{selectedNode.childCount}</span>
                    </div>
                )}
            </div>

            <div className="node-info-docstring">
                {selectedNode.docstring && <p>{selectedNode.docstring}</p>}
            </div>
        </div>
    );
}

export default NodeInfoPanel;
