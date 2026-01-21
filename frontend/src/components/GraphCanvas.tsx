/**
 * NeuroCode Graph Canvas Component
 *
 * Flow-based graph visualization with Sigma.js.
 * CRITICAL: Uses CSS to control canvas background for dark mode.
 */

import { useEffect, useCallback, useRef } from 'react';
import { SigmaContainer, useRegisterEvents, useSigma } from '@react-sigma/core';
import '@react-sigma/core/lib/react-sigma.min.css';

import { useGraphStore } from '@/stores/graphStore';
import { useThemeStore } from '@/stores/themeStore';

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
                const graph = sigma.getGraph();
                graph.setNodeAttribute(event.node, 'highlighted', true);
                graph.forEachEdge(event.node, (edge) => {
                    graph.setEdgeAttribute(edge, 'highlighted', true);
                });
                sigma.refresh();
            },
            leaveNode: (event) => {
                onNodeHover(null);
                const graph = sigma.getGraph();
                graph.setNodeAttribute(event.node, 'highlighted', false);
                graph.forEachEdge(event.node, (edge) => {
                    graph.setEdgeAttribute(edge, 'highlighted', false);
                });
                sigma.refresh();
            },
            doubleClickNode: (event) => {
                event.preventSigmaDefault();
                const nodeAttributes = sigma.getGraph().getNodeAttributes(event.node);
                sigma.getCamera().animate(
                    { x: nodeAttributes.x, y: nodeAttributes.y, ratio: 0.5 },
                    { duration: 400, easing: 'cubicInOut' },
                );
            },
        });
    }, [registerEvents, sigma, onNodeClick, onNodeHover]);

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
    const loadEntryPoint = useGraphStore((state) => state.loadEntryPoint);
    const isLoading = useGraphStore((state) => state.isLoading);

    const mode = useThemeStore((state) => state.mode);
    const isDark = mode === 'dark';

    const containerRef = useRef<HTMLDivElement>(null);

    // Load entry point on mount
    useEffect(() => {
        loadEntryPoint();
    }, [loadEntryPoint]);

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
                <p>Loading code flow...</p>
            </div>
        );
    }

    // Colors based on theme
    const labelColor = isDark ? '#f8fafc' : '#1e293b';
    const edgeColor = isDark ? 'rgba(148, 163, 184, 0.4)' : 'rgba(100, 116, 139, 0.5)';
    const edgeHighlightColor = isDark ? 'rgba(129, 140, 248, 0.9)' : 'rgba(79, 70, 229, 0.9)';
    const nodeDefaultColor = '#6366f1';

    // Canvas background style - CRITICAL for dark mode
    const canvasStyle: React.CSSProperties = {
        width: '100%',
        height: '100%',
        backgroundColor: isDark ? '#0a0a0f' : '#f8fafc',
    };

    return (
        <div
            ref={containerRef}
            className="graph-canvas"
            style={{ backgroundColor: isDark ? '#0a0a0f' : '#f8fafc' }}
        >
            <SigmaContainer
                graph={graph}
                style={canvasStyle}
                settings={{
                    allowInvalidContainer: true,
                    // Label settings
                    renderLabels: true,
                    labelRenderedSizeThreshold: 4,
                    labelSize: 14,
                    labelWeight: '600',
                    labelFont: 'Inter, -apple-system, system-ui, sans-serif',
                    labelColor: { color: labelColor },
                    // Default colors
                    defaultNodeColor: nodeDefaultColor,
                    defaultEdgeColor: edgeColor,
                    // Performance
                    enableEdgeEvents: false,
                    hideLabelsOnMove: false,
                    hideEdgesOnMove: false,
                    renderEdgeLabels: false,
                    // Camera
                    minCameraRatio: 0.05,
                    maxCameraRatio: 5,
                    stagePadding: 100,
                    // Node styling
                    nodeReducer: (_node, data) => {
                        const highlighted = data.highlighted || false;
                        const baseSize = data.size || 14;
                        return {
                            ...data,
                            size: highlighted ? baseSize * 1.3 : baseSize,
                            zIndex: highlighted ? 2 : 1,
                        };
                    },
                    // Edge styling with theme-aware colors
                    edgeReducer: (_edge, data) => {
                        const highlighted = data.highlighted || false;
                        return {
                            ...data,
                            size: highlighted ? 3 : 2,
                            color: highlighted ? edgeHighlightColor : edgeColor,
                        };
                    },
                }}
            >
                <GraphEvents onNodeClick={handleNodeClick} onNodeHover={handleNodeHover} />
            </SigmaContainer>
        </div>
    );
}

export default GraphCanvas;
