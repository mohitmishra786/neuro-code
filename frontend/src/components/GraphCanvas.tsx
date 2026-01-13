/**
 * NeuroCode Graph Canvas Component
 *
 * Main graph rendering component using Sigma.js + React-Sigma.
 */

import { useEffect, useCallback, useRef } from 'react';
import { SigmaContainer, useRegisterEvents, useSigma } from '@react-sigma/core';
import { useLayoutForceAtlas2 } from '@react-sigma/layout-forceatlas2';
import '@react-sigma/core/lib/react-sigma.min.css';

import { useGraphStore } from '@/stores/graphStore';
import { UI_COLORS } from '@/utils/colorScheme';

interface GraphEventsProps {
    onNodeClick: (nodeId: string) => void;
    onNodeHover: (nodeId: string | null) => void;
}

function GraphEvents({ onNodeClick, onNodeHover }: GraphEventsProps) {
    const registerEvents = useRegisterEvents();
    const sigma = useSigma();

    useEffect(() => {
        registerEvents({
            clickNode: (event) => {
                event.preventSigmaDefault();
                onNodeClick(event.node);
            },
            enterNode: (event) => {
                onNodeHover(event.node);
                sigma.getGraph().setNodeAttribute(event.node, 'highlighted', true);
                sigma.refresh();
            },
            leaveNode: (event) => {
                onNodeHover(null);
                sigma.getGraph().setNodeAttribute(event.node, 'highlighted', false);
                sigma.refresh();
            },
            doubleClickNode: (event) => {
                event.preventSigmaDefault();
                // Center on node
                const nodeAttributes = sigma.getGraph().getNodeAttributes(event.node);
                sigma.getCamera().animate(
                    { x: nodeAttributes.x, y: nodeAttributes.y, ratio: 0.5 },
                    { duration: 300 },
                );
            },
        });
    }, [registerEvents, sigma, onNodeClick, onNodeHover]);

    return null;
}

function ForceLayout() {
    const { start, stop, isRunning } = useLayoutForceAtlas2({
        settings: {
            gravity: 0.5,
            scalingRatio: 2,
            slowDown: 5,
            barnesHutOptimize: true,
            barnesHutTheta: 0.5,
        },
    });

    useEffect(() => {
        // Run layout briefly on mount
        start();
        const timeout = setTimeout(() => {
            stop();
        }, 2000);

        return () => {
            clearTimeout(timeout);
            if (isRunning) stop();
        };
    }, [start, stop, isRunning]);

    return null;
}

export function GraphCanvas() {
    const graph = useGraphStore((state) => state.graph);
    const expandNode = useGraphStore((state) => state.expandNode);
    const collapseNode = useGraphStore((state) => state.collapseNode);
    const selectNode = useGraphStore((state) => state.selectNode);
    const hoverNode = useGraphStore((state) => state.hoverNode);
    const nodes = useGraphStore((state) => state.nodes);
    const expandedNodes = useGraphStore((state) => state.expandedNodes);
    const loadRootNodes = useGraphStore((state) => state.loadRootNodes);
    const isLoading = useGraphStore((state) => state.isLoading);

    const containerRef = useRef<HTMLDivElement>(null);

    // Load root nodes on mount
    useEffect(() => {
        loadRootNodes();
    }, [loadRootNodes]);

    const handleNodeClick = useCallback(
        (nodeId: string) => {
            const node = nodes.get(nodeId);
            if (!node) return;

            selectNode(nodeId);

            // Toggle expand/collapse if node has children
            if (node.childCount > 0) {
                if (expandedNodes.has(nodeId)) {
                    collapseNode(nodeId);
                } else {
                    expandNode(nodeId);
                }
            }
        },
        [nodes, expandedNodes, selectNode, expandNode, collapseNode],
    );

    const handleNodeHover = useCallback(
        (nodeId: string | null) => {
            hoverNode(nodeId);
        },
        [hoverNode],
    );

    if (isLoading && graph.order === 0) {
        return (
            <div className="graph-canvas-loading">
                <div className="spinner" />
                <p>Loading graph...</p>
            </div>
        );
    }

    return (
        <div ref={containerRef} className="graph-canvas">
            <SigmaContainer
                graph={graph}
                style={{ width: '100%', height: '100%' }}
                settings={{
                    renderLabels: true,
                    labelRenderedSizeThreshold: 6,
                    labelSize: 12,
                    labelWeight: 'bold',
                    labelColor: { color: UI_COLORS.text },
                    defaultNodeColor: UI_COLORS.accent,
                    defaultEdgeColor: UI_COLORS.border,
                    nodeReducer: (node, data) => {
                        const highlighted = data.highlighted || false;
                        return {
                            ...data,
                            size: highlighted ? (data.size || 10) * 1.5 : data.size,
                            zIndex: highlighted ? 1 : 0,
                        };
                    },
                    edgeReducer: (edge, data) => {
                        return {
                            ...data,
                            size: 1,
                        };
                    },
                }}
            >
                <GraphEvents onNodeClick={handleNodeClick} onNodeHover={handleNodeHover} />
                <ForceLayout />
            </SigmaContainer>
        </div>
    );
}

export default GraphCanvas;
