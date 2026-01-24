/**
 * CircleNode Component
 *
 * Custom ReactFlow node that displays code elements as circles.
 * Features type-based colors, child count badges, and expand/collapse indicators.
 */

import { memo, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { NodeType } from '@/types/graph.types';
import { NODE_COLORS, useTreeStore } from '@/stores/treeStore';

interface CircleNodeData {
    label: string;
    nodeType: NodeType;
    childCount: number;
    isExpanded: boolean;
    isSelected: boolean;
    qualifiedName?: string;
    docstring?: string;
    isAsync?: boolean;
    complexity?: number;
}

// Alternative text icons for node types
const NodeLetters: Record<NodeType, string> = {
    package: 'P',
    module: 'M',
    class: 'C',
    function: 'F',
    variable: 'V',
    unknown: '?',
};

function CircleNodeComponent({ id, data, selected }: NodeProps<CircleNodeData>) {
    const toggleNode = useTreeStore((state) => state.toggleNode);
    const selectNode = useTreeStore((state) => state.selectNode);
    const isExpanding = useTreeStore((state) => state.isExpanding.has(id));
    
    const { label, nodeType, childCount, isExpanded, qualifiedName, isAsync, complexity } = data;
    
    const color = NODE_COLORS[nodeType] || NODE_COLORS.unknown;
    const icon = NodeLetters[nodeType] || '?';
    
    const handleClick = useCallback((e: React.MouseEvent) => {
        e.stopPropagation();
        selectNode(id);
    }, [id, selectNode]);
    
    const handleDoubleClick = useCallback((e: React.MouseEvent) => {
        e.stopPropagation();
        if (childCount > 0) {
            toggleNode(id);
        }
    }, [id, childCount, toggleNode]);
    
    return (
        <div 
            className={`circle-node ${selected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}`}
            onClick={handleClick}
            onDoubleClick={handleDoubleClick}
        >
            {/* Target handle at top */}
            <Handle
                type="target"
                position={Position.Top}
                className="circle-node-handle"
            />
            
            {/* Main circle */}
            <div 
                className="circle-node-circle"
                style={{ 
                    backgroundColor: color,
                    boxShadow: selected ? `0 0 0 3px ${color}40, 0 4px 20px ${color}60` : `0 4px 12px ${color}30`,
                }}
            >
                {/* Loading spinner */}
                {isExpanding ? (
                    <div className="circle-node-spinner" />
                ) : (
                    <span className="circle-node-icon">{icon}</span>
                )}
                
                {/* Async badge */}
                {isAsync && (
                    <span className="circle-node-async-badge" title="Async">⚡</span>
                )}
            </div>
            
            {/* Label */}
            <div className="circle-node-label" title={qualifiedName || label}>
                {label}
            </div>
            
            {/* Child count badge */}
            {childCount > 0 && (
                <div 
                    className={`circle-node-badge ${isExpanded ? 'expanded' : ''}`}
                    title={`${childCount} ${childCount === 1 ? 'child' : 'children'}`}
                >
                    {isExpanded ? '−' : childCount > 99 ? '99+' : childCount}
                </div>
            )}
            
            {/* Complexity indicator */}
            {complexity && complexity > 5 && (
                <div 
                    className="circle-node-complexity"
                    title={`Complexity: ${complexity}`}
                    style={{
                        backgroundColor: complexity > 10 ? '#ef4444' : '#f59e0b',
                    }}
                >
                    {complexity}
                </div>
            )}
            
            {/* Source handle at bottom */}
            <Handle
                type="source"
                position={Position.Bottom}
                className="circle-node-handle"
            />
        </div>
    );
}

export const CircleNode = memo(CircleNodeComponent);

export default CircleNode;
