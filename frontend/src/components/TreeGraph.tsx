/**
 * TreeGraph Component
 *
 * Main graph visualization using ReactFlow with dagre layout.
 * Supports lazy loading, circle nodes, and hierarchical tree layout.
 */

import { useEffect, useCallback, useMemo, useRef } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    NodeTypes,
    EdgeTypes,
    useReactFlow,
    ReactFlowProvider,
    BackgroundVariant,
    Node,
    Edge,
    Position,
    NodeChange,
    EdgeChange,
    applyNodeChanges,
    applyEdgeChanges,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';

import { CircleNode } from '@/components/nodes/CircleNode';
import { TypedEdge } from '@/components/edges/TypedEdge';
import { useTreeStore, NODE_COLORS } from '@/stores/treeStore';
import { useThemeStore } from '@/stores/themeStore';
import { isValidNodeType } from '@/types/graph.types';
import { ErrorBoundary } from '@/components/ErrorBoundary';

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

interface LayoutedElements {
    nodes: Node[];
    edges: Edge[];
}

function getLayoutedElements(nodes: Node[], edges: Edge[], direction = 'TB'): LayoutedElements {
    const isHorizontal = direction === 'LR';
    dagreGraph.setGraph({
        rankdir: direction,
        nodesep: 80,
        ranksep: 100,
        marginx: 50,
        marginy: 50,
    });

    for (const node of nodes) {
        dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    }

    for (const edge of edges) {
        dagreGraph.setEdge(edge.source, edge.target);
    }

    dagre.layout(dagreGraph);

    const layoutedNodes: Node[] = [];

    for (const node of nodes) {
        const nodeWithPosition = dagreGraph.node(node.id);
        if (!nodeWithPosition) {
            layoutedNodes.push(node);
            continue;
        }

        layoutedNodes.push({
            ...node,
            targetPosition: isHorizontal ? Position.Left : Position.Top,
            sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
            position: {
                x: nodeWithPosition.x - NODE_WIDTH / 2,
                y: nodeWithPosition.y - NODE_HEIGHT / 2,
            },
        });
    }

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
    const layoutedElements: LayoutedElements = useMemo(() => {
        if (nodes.length === 0) return { nodes: [], edges: [] };
        return getLayoutedElements(nodes, edges);
    }, [nodes, edges]);
    
    // Fit view when layout changes - with proper cleanup to prevent race conditions
    const fitViewTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    
    useEffect(() => {
        if (layoutedElements.nodes.length > 0) {
            // Cancel any pending fitView call
            if (fitViewTimeoutRef.current) {
                clearTimeout(fitViewTimeoutRef.current);
            }
            
            fitViewTimeoutRef.current = setTimeout(() => {
                fitView({ padding: 0.2, duration: 300 });
                fitViewTimeoutRef.current = null;
            }, 50);
        }
        
        return () => {
            if (fitViewTimeoutRef.current) {
                clearTimeout(fitViewTimeoutRef.current);
                fitViewTimeoutRef.current = null;
            }
        };
    }, [layoutedElements.nodes.length, fitView]);
    
    // Center on selected node - with proper cleanup to prevent race conditions
    const setCenterTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    
    useEffect(() => {
        if (selectedNodeId) {
            const selectedNode = layoutedElements.nodes.find(n => n.id === selectedNodeId);
            if (selectedNode) {
                // Cancel any pending setCenter call
                if (setCenterTimeoutRef.current) {
                    clearTimeout(setCenterTimeoutRef.current);
                }
                
                setCenterTimeoutRef.current = setTimeout(() => {
                    setCenter(
                        selectedNode.position.x + NODE_WIDTH / 2,
                        selectedNode.position.y + NODE_HEIGHT / 2,
                        { duration: 300, zoom: 1 }
                    );
                    setCenterTimeoutRef.current = null;
                }, 50);
            }
        }
        
        return () => {
            if (setCenterTimeoutRef.current) {
                clearTimeout(setCenterTimeoutRef.current);
                setCenterTimeoutRef.current = null;
            }
        };
    }, [selectedNodeId, layoutedElements.nodes, setCenter]);
    
    // Handle node click
    const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        selectNode(node.id);
    }, [selectNode]);

    // Handle node double click (expand/collapse)
    const handleNodeDoubleClick = useCallback((_: React.MouseEvent, node: Node) => {
        const nodeData = node.data;
        const childCount = typeof nodeData?.childCount === 'number' ? nodeData.childCount : 0;
        if (childCount > 0) {
            toggleNode(node.id);
        }
    }, [toggleNode]);
    
    // Handle pane click (deselect)
    const handlePaneClick = useCallback(() => {
        selectNode(null);
    }, [selectNode]);
    
    // MiniMap node color
    const minimapNodeColor = useCallback((node: Node): string => {
        const nodeType = node.data?.nodeType;
        if (typeof nodeType === 'string' && isValidNodeType(nodeType)) {
            return NODE_COLORS[nodeType];
        }
        return NODE_COLORS.unknown;
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
                <div className="empty-icon" aria-hidden>
                    🌳
                </div>
                <h3>No Code Structure</h3>
                <p>
                    Parse a Python codebase to visualize its architecture as a hierarchical
                    knowledge graph.
                </p>
                <div className="empty-cta">
                    <p className="empty-cta-label">Fastest path (from repo root):</p>
                    <pre className="empty-cta-code">
                        {`make demo
# or:
# python scripts/parse_codebase.py examples/demo_pkg --clear`}
                    </pre>
                    <p className="empty-cta-hint">
                        Desktop recommended. Double-click nodes with children to expand.
                    </p>
                    <a
                        className="empty-cta-link"
                        href="https://github.com/mohitmishra786/neuro-code/blob/main/docs/DEPLOYMENT.md"
                        target="_blank"
                        rel="noreferrer"
                    >
                        Full setup guide →
                    </a>
                </div>
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
                maskColor={isDark ? 'rgba(0, 0, 0, 0.75)' : 'rgba(255, 255, 255, 0.85)'}
                style={{
                    backgroundColor: isDark ? '#1a1a24' : '#f8fafc',
                }}
                position="bottom-right"
            />
        </ReactFlow>
    );
}

// Wrap with ReactFlowProvider and ErrorBoundary
export function TreeGraph() {
    return (
        <ReactFlowProvider>
            <ErrorBoundary
                fallback={
                    <div className="tree-graph-error">
                        <h3>Graph Error</h3>
                        <p>Failed to render the graph. Please try refreshing the page.</p>
                        <button onClick={() => window.location.reload()}>Refresh</button>
                    </div>
                }
            >
                <TreeGraphInner />
            </ErrorBoundary>
        </ReactFlowProvider>
    );
}

export default TreeGraph;
