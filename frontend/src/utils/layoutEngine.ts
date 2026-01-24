/**
 * NeuroCode Layout Engine
 *
 * Graph layout algorithms for node positioning.
 */

import { GraphNode } from '@/types/graph.types';

interface Position {
    x: number;
    y: number;
}

interface LayoutOptions {
    width?: number;
    height?: number;
    nodeSpacing?: number;
    levelSpacing?: number;
}

/**
 * Circular layout for children around a parent.
 */
export function circularLayout(
    parentPos: Position,
    childCount: number,
    options: LayoutOptions = {},
): Position[] {
    const { nodeSpacing = 100 } = options;

    if (childCount === 0) return [];
    if (childCount === 1) {
        return [{ x: parentPos.x, y: parentPos.y + nodeSpacing }];
    }

    const radius = nodeSpacing + Math.sqrt(childCount) * 20;
    const positions: Position[] = [];

    for (let i = 0; i < childCount; i++) {
        const angle = (2 * Math.PI * i) / childCount - Math.PI / 2;
        positions.push({
            x: parentPos.x + radius * Math.cos(angle),
            y: parentPos.y + radius * Math.sin(angle),
        });
    }

    return positions;
}

/**
 * Grid layout for root nodes.
 */
export function gridLayout(nodeCount: number, options: LayoutOptions = {}): Position[] {
    const { width = 800, height = 600, nodeSpacing = 150 } = options;

    if (nodeCount === 0) return [];

    const cols = Math.ceil(Math.sqrt(nodeCount * (width / height)));
    const rows = Math.ceil(nodeCount / cols);

    const positions: Position[] = [];
    const startX = -((cols - 1) * nodeSpacing) / 2;
    const startY = -((rows - 1) * nodeSpacing) / 2;

    for (let i = 0; i < nodeCount; i++) {
        const col = i % cols;
        const row = Math.floor(i / cols);
        positions.push({
            x: startX + col * nodeSpacing,
            y: startY + row * nodeSpacing,
        });
    }

    return positions;
}

/**
 * Hierarchical tree layout (top-down).
 */
export function treeLayout(
    nodes: Map<string, GraphNode>,
    rootId: string,
    options: LayoutOptions = {},
): Map<string, Position> {
    const { nodeSpacing = 80, levelSpacing = 120 } = options;
    const positions = new Map<string, Position>();

    function layoutSubtree(
        nodeId: string,
        depth: number,
        offset: number,
    ): { width: number; positions: Map<string, Position> } {
        const node = nodes.get(nodeId);
        if (!node) return { width: 0, positions: new Map() };

        // Find children (nodes that have this as parent in graph)
        const children: string[] = [];
        const nodeQualifiedName = node.qualifiedName || '';
        nodes.forEach((n, id) => {
            // This is simplified - in real implementation would use edge data
            const nQualifiedName = n.qualifiedName || '';
            if (nodeQualifiedName && nQualifiedName.startsWith(nodeQualifiedName + '.')) {
                const remaining = nQualifiedName.slice(nodeQualifiedName.length + 1);
                if (!remaining.includes('.')) {
                    children.push(id);
                }
            }
        });

        if (children.length === 0) {
            positions.set(nodeId, { x: offset, y: depth * levelSpacing });
            return { width: nodeSpacing, positions };
        }

        let currentX = offset;
        let totalWidth = 0;

        for (const childId of children) {
            const result = layoutSubtree(childId, depth + 1, currentX);
            result.positions.forEach((pos, id) => positions.set(id, pos));
            currentX += result.width;
            totalWidth += result.width;
        }

        // Position parent above children
        const parentX = offset + totalWidth / 2 - nodeSpacing / 2;
        positions.set(nodeId, { x: parentX, y: depth * levelSpacing });

        return { width: totalWidth, positions };
    }

    layoutSubtree(rootId, 0, 0);
    return positions;
}

/**
 * Force-directed layout settings generator.
 */
export function getForceLayoutSettings(nodeCount: number) {
    // Adjust settings based on graph size
    if (nodeCount < 50) {
        return {
            gravity: 1,
            scalingRatio: 1,
            slowDown: 3,
            barnesHutOptimize: false,
        };
    } else if (nodeCount < 200) {
        return {
            gravity: 0.5,
            scalingRatio: 2,
            slowDown: 5,
            barnesHutOptimize: true,
            barnesHutTheta: 0.5,
        };
    } else {
        return {
            gravity: 0.3,
            scalingRatio: 5,
            slowDown: 10,
            barnesHutOptimize: true,
            barnesHutTheta: 0.8,
        };
    }
}

/**
 * Calculate node size based on importance.
 */
export function calculateNodeSize(
    node: GraphNode,
    options: { minSize?: number; maxSize?: number } = {},
): number {
    const { minSize = 6, maxSize = 20 } = options;

    // Base size on child count and type
    let size = minSize;

    if (node.childCount > 0) {
        size += Math.log(node.childCount + 1) * 3;
    }

    if (node.type === 'module') {
        size *= 1.5;
    } else if (node.type === 'class') {
        size *= 1.2;
    }

    return Math.min(size, maxSize);
}

/**
 * Calculate edge weight for layout.
 */
export function calculateEdgeWeight(
    _sourceType: string,
    _targetType: string,
    relationshipType: string,
): number {
    // Stronger weight = closer together
    if (relationshipType === 'CONTAINS') {
        return 2.0;
    } else if (relationshipType === 'INHERITS') {
        return 1.5;
    } else if (relationshipType === 'CALLS') {
        return 1.0;
    } else if (relationshipType === 'IMPORTS') {
        return 0.5;
    }
    return 0.3;
}
