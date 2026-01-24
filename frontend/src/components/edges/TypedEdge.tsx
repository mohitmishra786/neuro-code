/**
 * TypedEdge Component
 *
 * Custom ReactFlow edge with different styles based on relationship type.
 * - CONTAINS: Solid line (hierarchy)
 * - CALLS: Dashed animated line (function calls)
 * - IMPORTS: Dotted line (module imports)
 * - INHERITS: Thick solid line (class inheritance)
 */

import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';

interface TypedEdgeData {
    edgeType?: 'contains' | 'calls' | 'imports' | 'inherits';
    label?: string;
}

// Edge colors by type
const EDGE_COLORS = {
    contains: '#64748b',  // Slate gray
    calls: '#f59e0b',     // Amber
    imports: '#6366f1',   // Indigo
    inherits: '#10b981',  // Emerald
};

// Edge styles
const EDGE_STYLES = {
    contains: {
        strokeWidth: 2,
        strokeDasharray: undefined,
        animated: false,
    },
    calls: {
        strokeWidth: 1.5,
        strokeDasharray: '5,5',
        animated: true,
    },
    imports: {
        strokeWidth: 1.5,
        strokeDasharray: '3,3',
        animated: false,
    },
    inherits: {
        strokeWidth: 3,
        strokeDasharray: undefined,
        animated: false,
    },
};

function TypedEdgeComponent({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    style = {},
    markerEnd,
    selected,
}: EdgeProps<TypedEdgeData>) {
    const edgeType = data?.edgeType || 'contains';
    const color = EDGE_COLORS[edgeType];
    const edgeStyle = EDGE_STYLES[edgeType];
    
    const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });
    
    return (
        <>
            {/* Invisible wider path for easier selection */}
            <path
                id={`${id}-selector`}
                className="react-flow__edge-path"
                d={edgePath}
                style={{
                    strokeWidth: 20,
                    stroke: 'transparent',
                    fill: 'none',
                }}
            />
            
            {/* Main edge path */}
            <path
                id={id}
                className={`typed-edge typed-edge-${edgeType} ${selected ? 'selected' : ''}`}
                d={edgePath}
                style={{
                    ...style,
                    stroke: color,
                    strokeWidth: selected ? edgeStyle.strokeWidth + 1 : edgeStyle.strokeWidth,
                    strokeDasharray: edgeStyle.strokeDasharray,
                    fill: 'none',
                    filter: selected ? `drop-shadow(0 0 4px ${color})` : undefined,
                }}
                markerEnd={markerEnd}
            />
            
            {/* Animated dash for calls */}
            {edgeStyle.animated && (
                <path
                    className="typed-edge-animated"
                    d={edgePath}
                    style={{
                        stroke: color,
                        strokeWidth: edgeStyle.strokeWidth,
                        strokeDasharray: '5,5',
                        fill: 'none',
                        animation: 'dash 1s linear infinite',
                    }}
                />
            )}
            
            {/* Edge label */}
            {data?.label && (
                <EdgeLabelRenderer>
                    <div
                        className="typed-edge-label"
                        style={{
                            position: 'absolute',
                            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
                            background: color,
                            color: 'white',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 500,
                            pointerEvents: 'none',
                        }}
                    >
                        {data.label}
                    </div>
                </EdgeLabelRenderer>
            )}
        </>
    );
}

export const TypedEdge = memo(TypedEdgeComponent);

export default TypedEdge;
