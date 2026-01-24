/**
 * TreeGraph Component
 *
 * Main graph visualization using ReactFlow with dagre layout.
 * Supports lazy loading, circle nodes, and hierarchical tree layout.
 */

import { useEffect, useCallback, useMemo } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    NodeTypes,
    EdgeTypes,
    useReactFlow,
    ReactFlowProvider,
    BackgroundVariant,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';

import { CircleNode } from '@/components/nodes/CircleNode';
import { TypedEdge } from '@/components/edges/TypedEdge';
import { useTreeStore, NODE_COLORS } from '@/stores/treeStore';
import { useThemeStore } from '@/stores/themeStore';
import { NodeType } from '@/types/graph.types';

// Register custom node types
const nodeTypes: NodeTypes = {
    circleNode: CircleNode,
};

// Register custom edge types
const edgeTypes: EdgeTypes = {
    typed: TypedEdge,
};

// Dagre layout configuration
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const NODE_WIDTH = 120;
const NODE_HEIGHT = 100;

function getLayoutedElements(nodes: any[], edges: any[], direction = 'TB') {
    const isHorizontal = direction === 'LR';
    dagreGraph.setGraph({ 
        rankdir: direction,
        nodesep: 80,
        ranksep: 100,
        marginx: 50,
        marginy: 50,
    });

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        if (!nodeWithPosition) {
            return node;
        }
        
        return {
            ...node,
            targetPosition: isHorizontal ? 'left' : 'top',
            sourcePosition: isHorizontal ? 'right' : 'bottom',
            position: {
                x: nodeWithPosition.x - NODE_WIDTH / 2,
                y: nodeWithPosition.y - NODE_HEIGHT / 2,
            },
        };
    });

    return { nodes: layoutedNodes, edges };
}

function TreeGraphInner() {
    const { fitView, setCenter } = useReactFlow();
    
    const nodes = useTreeStore((state) => state.nodes);
    const edges = useTreeStore((state) => state.edges);
    const isLoading = useTreeStore((state) => state.isLoading);
    const error = useTreeStore((state) => state.error);
    const selectedNodeId = useTreeStore((state) => state.selectedNodeId);
    const loadRootNodes = useTreeStore((state) => state.loadRootNodes);
    const onNodesChange = useTreeStore((state) => state.onNodesChange);
    const onEdgesChange = useTreeStore((state) => state.onEdgesChange);
    const selectNode = useTreeStore((state) => state.selectNode);
    const toggleNode = useTreeStore((state) => state.toggleNode);
    
    const mode = useThemeStore((state) => state.mode);
    const isDark = mode === 'dark';
    
    // Load root nodes on mount
    useEffect(() => {
        loadRootNodes();
    }, [loadRootNodes]);
    
    // Apply dagre layout when nodes/edges change
    const layoutedElements = useMemo(() => {
        if (nodes.length === 0) return { nodes: [], edges: [] };
        return getLayoutedElements(nodes, edges);
    }, [nodes, edges]);
    
    // Fit view when layout changes
    useEffect(() => {
        if (layoutedElements.nodes.length > 0) {
            setTimeout(() => {
                fitView({ padding: 0.2, duration: 300 });
            }, 50);
        }
    }, [layoutedElements.nodes.length, fitView]);
    
    // Center on selected node
    useEffect(() => {
        if (selectedNodeId) {
            const selectedNode = layoutedElements.nodes.find(n => n.id === selectedNodeId);
            if (selectedNode) {
                setCenter(
                    selectedNode.position.x + NODE_WIDTH / 2,
                    selectedNode.position.y + NODE_HEIGHT / 2,
                    { duration: 300, zoom: 1 }
                );
            }
        }
    }, [selectedNodeId, layoutedElements.nodes, setCenter]);
    
    // Handle node click
    const handleNodeClick = useCallback((_: React.MouseEvent, node: any) => {
        selectNode(node.id);
    }, [selectNode]);
    
    // Handle node double click (expand/collapse)
    const handleNodeDoubleClick = useCallback((_: React.MouseEvent, node: any) => {
        const nodeData = node.data;
        if (nodeData.childCount > 0) {
            toggleNode(node.id);
        }
    }, [toggleNode]);
    
    // Handle pane click (deselect)
    const handlePaneClick = useCallback(() => {
        selectNode(null);
    }, [selectNode]);
    
    // MiniMap node color
    const minimapNodeColor = useCallback((node: any) => {
            const nodeType: NodeType = node.data?.nodeType as NodeType;
            return NODE_COLORS[nodeType] || NODE_COLORS.unknown;
    }, []);
    
    if (isLoading && nodes.length === 0) {
        return (
            <div className="tree-graph-loading">
                <div className="spinner" />
                <p>Loading code structure...</p>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className="tree-graph-error">
                <p>Error: {error}</p>
                <button onClick={() => loadRootNodes()}>Retry</button>
            </div>
        );
    }
    
    if (nodes.length === 0) {
        return (
            <div className="tree-graph-empty">
                <div className="empty-icon">🌳</div>
                <h3>No Code Structure</h3>
                <p>Parse a Python codebase to visualize its structure.</p>
            </div>
        );
    }
    
    return (
        <ReactFlow
            nodes={layoutedElements.nodes}
            edges={layoutedElements.edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            onNodeDoubleClick={handleNodeDoubleClick}
            onPaneClick={handlePaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.1}
            maxZoom={2}
            defaultEdgeOptions={{
                type: 'smoothstep',
                animated: false,
            }}
            proOptions={{ hideAttribution: true }}
            className={`tree-graph ${isDark ? 'dark' : 'light'}`}
        >
            <Background 
                variant={BackgroundVariant.Dots}
                gap={20}
                size={1}
                color={isDark ? '#333' : '#ddd'}
            />
            <Controls 
                showZoom={true}
                showFitView={true}
                showInteractive={false}
                position="bottom-left"
            />
            <MiniMap 
                nodeColor={minimapNodeColor}
                maskColor={isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.8)'}
                style={{
                    backgroundColor: isDark ? '#1a1a24' : '#f8fafc',
                }}
                position="bottom-right"
            />
        </ReactFlow>
    );
}

// Wrap with ReactFlowProvider
export function TreeGraph() {
    return (
        <ReactFlowProvider>
            <TreeGraphInner />
        </ReactFlowProvider>
    );
}

export default TreeGraph;
