/**
 * TypedEdge Component
 *
 * Custom ReactFlow edge with different styles based on relationship type.
 * - contains: Solid line (hierarchy)
 * - calls: Dashed animated line (function calls)
 * - imports: Dotted line (module imports)
 * - inherits: Thick solid line (class inheritance)
 */

import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';
import { EdgeType } from '@/types/graph.types';

interface TypedEdgeData {
    edgeType?: EdgeType;
    label?: string;
}

export const NODE_TYPE_CIRCLE = 'circleNode' as const;

const EDGE_COLORS: Record<EdgeType, string> = {
    contains: '#64748b',
    calls: '#f59e0b',
    imports: '#6366f1',
    inherits: '#10b981',
};

interface EdgeStyleConfig {
    strokeWidth: number;
    strokeDasharray: string | undefined;
    animated: boolean;
}

const EDGE_STYLES: Record<EdgeType, EdgeStyleConfig> = {
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
