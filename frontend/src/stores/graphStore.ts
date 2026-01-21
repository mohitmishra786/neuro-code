/**
 * NeuroCode Graph Store
 *
 * Zustand store for flow-based graph visualization.
 * Starts from entry point and expands hierarchically.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import Graph from 'graphology';

import { GraphNode, SearchResult, BreadcrumbItem } from '@/types/graph.types';
import { api } from '@/services/api';
import { getNodeColor } from '@/utils/colorScheme';

interface GraphState {
    // Graph data
    graph: Graph;
    nodes: Map<string, GraphNode>;
    expandedNodes: Set<string>;
    allModules: GraphNode[];

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
    loadEntryPoint: () => Promise<void>;
    expandNode: (nodeId: string) => Promise<void>;
    collapseNode: (nodeId: string) => void;
    selectNode: (nodeId: string | null) => void;
    hoverNode: (nodeId: string | null) => void;
    searchNodes: (query: string) => Promise<void>;
    focusNode: (nodeId: string) => Promise<void>;
    refresh: () => Promise<void>;
    reset: () => void;
}

// Layout constants
const ENTRY_POINT_SIZE = 32;
const MODULE_SIZE = 22;
const CHILD_SIZE = 16;
const FUNCTION_SIZE = 14;

// Spacing constants - much larger for no overlap
const INITIAL_SPACING = 300;
const CHILD_RADIUS = 250;

// Get node size based on type
function getNodeSize(type: string, childCount: number): number {
    let base: number;
    switch (type) {
        case 'module':
            base = MODULE_SIZE;
            break;
        case 'class':
            base = CHILD_SIZE;
            break;
        case 'function':
            base = FUNCTION_SIZE;
            break;
        default:
            base = FUNCTION_SIZE;
    }
    return base + Math.min(Math.sqrt(childCount) * 2, 8);
}

export const useGraphStore = create<GraphState>()(
    devtools(
        subscribeWithSelector((set, get) => ({
            // Initial state
            graph: new Graph(),
            nodes: new Map(),
            expandedNodes: new Set(),
            allModules: [],
            selectedNodeId: null,
            hoveredNodeId: null,
            breadcrumbs: [],
            isLoading: false,
            isExpanding: new Set(),
            error: null,
            searchResults: [],
            searchQuery: '',

            // Load entry point - SIMPLIFIED
            loadEntryPoint: async () => {
                const { graph, nodes } = get();
                set({ isLoading: true, error: null });

                try {
                    console.log('[NeuroCode] Loading entry point...');
                    const { entryPoint, imports, allModules } = await api.getEntryPoint();
                    console.log('[NeuroCode] Entry point:', entryPoint?.name, 'Imports:', imports.length);

                    set({ allModules });

                    if (!entryPoint) {
                        console.log('[NeuroCode] No entry point found, showing empty');
                        set({ isLoading: false });
                        return;
                    }

                    // Add entry point at center
                    const enrichedEntry: GraphNode = {
                        ...entryPoint,
                        x: 0,
                        y: 0,
                        size: ENTRY_POINT_SIZE,
                        color: getNodeColor(entryPoint.type),
                        label: entryPoint.name,
                    };

                    nodes.set(entryPoint.id, enrichedEntry);

                    if (!graph.hasNode(entryPoint.id)) {
                        graph.addNode(entryPoint.id, {
                            x: 0,
                            y: 0,
                            size: ENTRY_POINT_SIZE,
                            color: enrichedEntry.color,
                            label: enrichedEntry.label,
                            nodeType: enrichedEntry.type,
                        });
                    }

                    // Add imports to the right
                    imports.forEach((imp, index) => {
                        const y = (index - (imports.length - 1) / 2) * 100;
                        const impSize = getNodeSize(imp.type, imp.childCount);

                        const enrichedImport: GraphNode = {
                            ...imp,
                            x: INITIAL_SPACING,
                            y: y,
                            size: impSize,
                            color: getNodeColor(imp.type),
                            label: imp.name,
                        };

                        nodes.set(imp.id, enrichedImport);

                        if (!graph.hasNode(imp.id)) {
                            graph.addNode(imp.id, {
                                x: INITIAL_SPACING,
                                y: y,
                                size: impSize,
                                color: enrichedImport.color,
                                label: enrichedImport.label,
                                nodeType: enrichedImport.type,
                            });
                        }

                        // Add edge safely
                        const edgeId = `${entryPoint.id}->import->${imp.id}`;
                        try {
                            if (!graph.hasEdge(edgeId) && !graph.hasEdge(entryPoint.id, imp.id)) {
                                graph.addEdge(entryPoint.id, imp.id, {
                                    id: edgeId,
                                    edgeType: 'IMPORTS',
                                });
                            }
                        } catch {
                            // Edge already exists, ignore
                        }
                    });

                    console.log('[NeuroCode] Graph loaded with', graph.order, 'nodes');
                    set({ nodes: new Map(nodes), isLoading: false });

                } catch (error) {
                    console.error('[NeuroCode] Error loading entry point:', error);
                    set({
                        isLoading: false,
                        error: error instanceof Error ? error.message : 'Failed to load entry point',
                    });
                }
            },

            // Expand a node to show its children
            expandNode: async (nodeId: string) => {
                const { graph, nodes, expandedNodes, isExpanding } = get();

                if (expandedNodes.has(nodeId) || isExpanding.has(nodeId)) {
                    return;
                }

                const parentNode = nodes.get(nodeId);
                if (!parentNode || parentNode.x === undefined || parentNode.y === undefined) {
                    return;
                }

                isExpanding.add(nodeId);
                set({ isExpanding: new Set(isExpanding) });

                try {
                    console.log('[NeuroCode] Expanding node:', parentNode.name);
                    const children = await api.getNodeChildren(nodeId);
                    console.log('[NeuroCode] Got', children.length, 'children');

                    // Update parent size
                    parentNode.isExpanded = true;
                    if (graph.hasNode(nodeId)) {
                        graph.setNodeAttribute(nodeId, 'size', (parentNode.size || 20) + 6);
                        graph.setNodeAttribute(nodeId, 'color', getNodeColor(parentNode.type, true));
                    }

                    // Calculate positions - radial layout with large radius
                    const radius = CHILD_RADIUS + children.length * 10;

                    children.forEach((child, index) => {
                        // Calculate angle - distribute evenly in a circle
                        const angle = (2 * Math.PI * index) / children.length - Math.PI / 2;
                        const x = parentNode.x! + radius * Math.cos(angle);
                        const y = parentNode.y! + radius * Math.sin(angle);

                        const childSize = getNodeSize(child.type, child.childCount);

                        const enrichedChild: GraphNode = {
                            ...child,
                            x,
                            y,
                            size: childSize,
                            color: getNodeColor(child.type),
                            label: child.name,
                        };

                        nodes.set(child.id, enrichedChild);

                        if (!graph.hasNode(child.id)) {
                            graph.addNode(child.id, {
                                x,
                                y,
                                size: childSize,
                                color: enrichedChild.color,
                                label: enrichedChild.label,
                                nodeType: enrichedChild.type,
                            });
                        }

                        // Add edge safely
                        const edgeId = `${nodeId}->${child.id}`;
                        try {
                            if (!graph.hasEdge(edgeId) && !graph.hasEdge(nodeId, child.id)) {
                                graph.addEdge(nodeId, child.id, {
                                    id: edgeId,
                                    edgeType: 'CONTAINS',
                                });
                            }
                        } catch {
                            // Edge already exists, ignore
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
                    console.error('[NeuroCode] Error expanding node:', error);
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

                // Collect descendants to remove
                const toRemove = new Set<string>();
                function collectDescendants(id: string) {
                    for (const edge of graph.outEdges(id)) {
                        const target = graph.target(edge);
                        if (!toRemove.has(target)) {
                            toRemove.add(target);
                            collectDescendants(target);
                        }
                    }
                }
                collectDescendants(nodeId);

                // Remove descendants
                for (const id of toRemove) {
                    if (graph.hasNode(id)) {
                        graph.dropNode(id);
                    }
                    nodes.delete(id);
                    expandedNodes.delete(id);
                }

                // Update parent
                parentNode.isExpanded = false;
                if (graph.hasNode(nodeId)) {
                    graph.setNodeAttribute(nodeId, 'size', getNodeSize(parentNode.type, parentNode.childCount));
                    graph.setNodeAttribute(nodeId, 'color', getNodeColor(parentNode.type));
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
                } catch {
                    set({ searchResults: [] });
                }
            },

            focusNode: async (nodeId: string) => {
                const { nodes, expandNode, selectNode } = get();

                try {
                    const ancestors = await api.getNodeAncestors(nodeId);
                    for (const ancestor of ancestors) {
                        if (!nodes.has(ancestor.id)) {
                            await get().loadEntryPoint();
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
                const { reset, loadEntryPoint } = get();
                reset();
                await loadEntryPoint();
            },

            reset: () => {
                set({
                    graph: new Graph(),
                    nodes: new Map(),
                    expandedNodes: new Set(),
                    allModules: [],
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
