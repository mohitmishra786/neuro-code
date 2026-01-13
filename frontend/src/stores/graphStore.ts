/**
 * NeuroCode Graph Store
 *
 * Zustand store for graph state management.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import Graph from 'graphology';

import { GraphNode, GraphEdge, NodeType, SearchResult, BreadcrumbItem } from '@/types/graph.types';
import { api } from '@/services/api';
import { getNodeColor } from '@/utils/colorScheme';

interface GraphState {
    // Graph data
    graph: Graph;
    nodes: Map<string, GraphNode>;
    expandedNodes: Set<string>;

    // Selection
    selectedNodeId: string | null;
    hoveredNodeId: string | null;

    // Navigation
    breadcrumbs: BreadcrumbItem[];

    // Loading states
    isLoading: boolean;
    isExpanding: Set<string>;
    error: string | null;

    // Search
    searchResults: SearchResult[];
    searchQuery: string;

    // Actions
    loadRootNodes: () => Promise<void>;
    expandNode: (nodeId: string) => Promise<void>;
    collapseNode: (nodeId: string) => void;
    selectNode: (nodeId: string | null) => void;
    hoverNode: (nodeId: string | null) => void;
    searchNodes: (query: string) => Promise<void>;
    focusNode: (nodeId: string) => Promise<void>;
    refresh: () => Promise<void>;
    reset: () => void;
}

const INITIAL_NODE_SIZE = 10;
const EXPANDED_NODE_SIZE = 15;
const ROOT_SPACING = 150;

function calculateNodePosition(
    parentNode: GraphNode | null,
    childIndex: number,
    totalChildren: number,
): { x: number; y: number } {
    if (!parentNode || parentNode.x === undefined || parentNode.y === undefined) {
        // Root level: arrange in a grid
        const cols = Math.ceil(Math.sqrt(totalChildren));
        const row = Math.floor(childIndex / cols);
        const col = childIndex % cols;
        return {
            x: col * ROOT_SPACING - (cols * ROOT_SPACING) / 2,
            y: row * ROOT_SPACING - (Math.ceil(totalChildren / cols) * ROOT_SPACING) / 2,
        };
    }

    // Child nodes: arrange in a circle around parent
    const radius = 80 + Math.sqrt(totalChildren) * 20;
    const angle = (2 * Math.PI * childIndex) / totalChildren - Math.PI / 2;
    return {
        x: parentNode.x + radius * Math.cos(angle),
        y: parentNode.y + radius * Math.sin(angle),
    };
}

export const useGraphStore = create<GraphState>()(
    devtools(
        subscribeWithSelector((set, get) => ({
            // Initial state
            graph: new Graph(),
            nodes: new Map(),
            expandedNodes: new Set(),
            selectedNodeId: null,
            hoveredNodeId: null,
            breadcrumbs: [],
            isLoading: false,
            isExpanding: new Set(),
            error: null,
            searchResults: [],
            searchQuery: '',

            loadRootNodes: async () => {
                const { graph, nodes } = get();

                set({ isLoading: true, error: null });

                try {
                    const rootNodes = await api.getRootNodes();

                    // Add root nodes to graph
                    rootNodes.forEach((node, index) => {
                        const position = calculateNodePosition(null, index, rootNodes.length);
                        const enrichedNode: GraphNode = {
                            ...node,
                            x: position.x,
                            y: position.y,
                            size: INITIAL_NODE_SIZE,
                            color: getNodeColor(node.type),
                            label: node.name,
                        };

                        nodes.set(node.id, enrichedNode);

                        if (!graph.hasNode(node.id)) {
                            graph.addNode(node.id, {
                                x: enrichedNode.x,
                                y: enrichedNode.y,
                                size: enrichedNode.size,
                                color: enrichedNode.color,
                                label: enrichedNode.label,
                                type: enrichedNode.type,
                            });
                        }
                    });

                    set({ nodes: new Map(nodes), isLoading: false });
                } catch (error) {
                    set({
                        isLoading: false,
                        error: error instanceof Error ? error.message : 'Failed to load nodes',
                    });
                }
            },

            expandNode: async (nodeId: string) => {
                const { graph, nodes, expandedNodes, isExpanding } = get();

                // Skip if already expanded or currently expanding
                if (expandedNodes.has(nodeId) || isExpanding.has(nodeId)) {
                    return;
                }

                const parentNode = nodes.get(nodeId);
                if (!parentNode) {
                    return;
                }

                // Mark as expanding
                isExpanding.add(nodeId);
                set({ isExpanding: new Set(isExpanding) });

                try {
                    const children = await api.getNodeChildren(nodeId);

                    // Update parent node
                    parentNode.isExpanded = true;
                    parentNode.size = EXPANDED_NODE_SIZE;
                    parentNode.color = getNodeColor(parentNode.type, true);

                    if (graph.hasNode(nodeId)) {
                        graph.setNodeAttribute(nodeId, 'size', EXPANDED_NODE_SIZE);
                        graph.setNodeAttribute(nodeId, 'color', parentNode.color);
                    }

                    // Add child nodes
                    children.forEach((child, index) => {
                        const position = calculateNodePosition(parentNode, index, children.length);
                        const enrichedChild: GraphNode = {
                            ...child,
                            x: position.x,
                            y: position.y,
                            size: INITIAL_NODE_SIZE,
                            color: getNodeColor(child.type),
                            label: child.name,
                        };

                        nodes.set(child.id, enrichedChild);

                        if (!graph.hasNode(child.id)) {
                            graph.addNode(child.id, {
                                x: enrichedChild.x,
                                y: enrichedChild.y,
                                size: enrichedChild.size,
                                color: enrichedChild.color,
                                label: enrichedChild.label,
                                type: enrichedChild.type,
                            });
                        }

                        // Add edge from parent to child
                        const edgeId = `${nodeId}->${child.id}`;
                        if (!graph.hasEdge(edgeId)) {
                            graph.addEdge(nodeId, child.id, {
                                id: edgeId,
                                type: 'CONTAINS',
                                color: '#E0E0E0',
                            });
                        }
                    });

                    expandedNodes.add(nodeId);
                    isExpanding.delete(nodeId);

                    set({
                        nodes: new Map(nodes),
                        expandedNodes: new Set(expandedNodes),
                        isExpanding: new Set(isExpanding),
                    });
                } catch (error) {
                    isExpanding.delete(nodeId);
                    set({
                        isExpanding: new Set(isExpanding),
                        error: error instanceof Error ? error.message : 'Failed to expand node',
                    });
                }
            },

            collapseNode: (nodeId: string) => {
                const { graph, nodes, expandedNodes } = get();

                if (!expandedNodes.has(nodeId)) {
                    return;
                }

                const parentNode = nodes.get(nodeId);
                if (!parentNode) {
                    return;
                }

                // Find and remove all descendants
                const toRemove = new Set<string>();

                function collectDescendants(id: string) {
                    const edges = graph.outEdges(id);
                    for (const edge of edges) {
                        const target = graph.target(edge);
                        if (!toRemove.has(target)) {
                            toRemove.add(target);
                            collectDescendants(target);
                        }
                    }
                }

                collectDescendants(nodeId);

                // Remove descendant nodes
                for (const id of toRemove) {
                    if (graph.hasNode(id)) {
                        graph.dropNode(id);
                    }
                    nodes.delete(id);
                    expandedNodes.delete(id);
                }

                // Update parent node
                parentNode.isExpanded = false;
                parentNode.size = INITIAL_NODE_SIZE;
                parentNode.color = getNodeColor(parentNode.type);

                if (graph.hasNode(nodeId)) {
                    graph.setNodeAttribute(nodeId, 'size', INITIAL_NODE_SIZE);
                    graph.setNodeAttribute(nodeId, 'color', parentNode.color);
                }

                expandedNodes.delete(nodeId);

                set({
                    nodes: new Map(nodes),
                    expandedNodes: new Set(expandedNodes),
                });
            },

            selectNode: (nodeId: string | null) => {
                set({ selectedNodeId: nodeId });

                if (nodeId) {
                    // Update breadcrumbs
                    api.getNodeAncestors(nodeId).then((ancestors) => {
                        const breadcrumbs = ancestors.map((a) => ({
                            id: a.id,
                            name: a.name,
                            type: a.type,
                        }));
                        set({ breadcrumbs });
                    });
                } else {
                    set({ breadcrumbs: [] });
                }
            },

            hoverNode: (nodeId: string | null) => {
                set({ hoveredNodeId: nodeId });
            },

            searchNodes: async (query: string) => {
                set({ searchQuery: query });

                if (!query.trim()) {
                    set({ searchResults: [] });
                    return;
                }

                try {
                    const response = await api.search(query);
                    set({ searchResults: response.results });
                } catch (error) {
                    set({ searchResults: [] });
                }
            },

            focusNode: async (nodeId: string) => {
                const { nodes, expandNode, selectNode } = get();

                // First, ensure the node is visible by expanding its ancestors
                try {
                    const ancestors = await api.getNodeAncestors(nodeId);

                    // Expand each ancestor in order
                    for (const ancestor of ancestors) {
                        if (!nodes.has(ancestor.id)) {
                            // Need to load this node first
                            await get().loadRootNodes();
                        }
                        await expandNode(ancestor.id);
                    }

                    selectNode(nodeId);
                } catch (error) {
                    set({
                        error: error instanceof Error ? error.message : 'Failed to focus node',
                    });
                }
            },

            refresh: async () => {
                const { reset, loadRootNodes } = get();
                reset();
                await loadRootNodes();
            },

            reset: () => {
                set({
                    graph: new Graph(),
                    nodes: new Map(),
                    expandedNodes: new Set(),
                    selectedNodeId: null,
                    hoveredNodeId: null,
                    breadcrumbs: [],
                    isLoading: false,
                    isExpanding: new Set(),
                    error: null,
                    searchResults: [],
                    searchQuery: '',
                });
            },
        })),
        { name: 'NeuroCodeGraph' },
    ),
);

export default useGraphStore;
