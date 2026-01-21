/**
 * NeuroCode Graph Store
 *
 * Zustand store for flow-based graph visualization.
 * Uses dagre for DAG layout and incremental loading.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import Graph from 'graphology';
import dagre from 'dagre';

import { GraphNode, SearchResult, BreadcrumbItem, NodeType } from '@/types/graph.types';
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

// Spacing constants
const HORIZONTAL_SPACING = 200;
const VERTICAL_SPACING = 80;

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

// Apply dagre layout to position nodes
function applyDagreLayout(graph: Graph): void {
    if (graph.order === 0) return;

    const g = new dagre.graphlib.Graph();
    g.setGraph({
        rankdir: 'LR', // Left to right
        ranksep: HORIZONTAL_SPACING,
        nodesep: VERTICAL_SPACING,
        marginx: 50,
        marginy: 50,
    });
    g.setDefaultEdgeLabel(() => ({}));

    // Add nodes
    graph.forEachNode((nodeId, attrs) => {
        g.setNode(nodeId, {
            width: (attrs.size || 20) * 3,
            height: (attrs.size || 20) * 2,
        });
    });

    // Add edges
    graph.forEachEdge((_edge, _attrs, source, target) => {
        g.setEdge(source, target);
    });

    // Run layout
    dagre.layout(g);

    // Apply positions
    g.nodes().forEach((nodeId: string) => {
        const node = g.node(nodeId);
        if (node && graph.hasNode(nodeId)) {
            graph.setNodeAttribute(nodeId, 'x', node.x);
            graph.setNodeAttribute(nodeId, 'y', node.y);
        }
    });
}

// Extract display name from hierarchical ID
function getDisplayName(id: string, name: string): string {
    // If it's a file path like "vaak/core/math_engine.py", show just the name
    if (id.includes('/') && !id.includes('::')) {
        return name;
    }
    // If it's a nested item like "vaak/core/math_engine.py::SomeClass", show the last part
    if (id.includes('::')) {
        const parts = id.split('::');
        return parts[parts.length - 1];
    }
    return name;
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

            // Load entry point
            loadEntryPoint: async () => {
                const { graph, nodes } = get();
                set({ isLoading: true, error: null });

                try {
                    console.log('[NeuroCode] Loading entry point...');
                    const { entryPoint, imports, allModules } = await api.getEntryPoint();
                    console.log('[NeuroCode] Entry point:', entryPoint?.name, 'Imports:', imports.length);

                    set({ allModules });

                    if (!entryPoint) {
                        console.log('[NeuroCode] No entry point found');
                        set({ isLoading: false });
                        return;
                    }

                    // Add entry point
                    const enrichedEntry: GraphNode = {
                        ...entryPoint,
                        x: 0,
                        y: 0,
                        size: ENTRY_POINT_SIZE,
                        color: getNodeColor(entryPoint.type),
                        label: getDisplayName(entryPoint.id, entryPoint.name),
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

                    // Add ALL modules (not just imports) for 100% codebase visibility
                    // This ensures validators.py and all other modules are visible
                    allModules.forEach((mod) => {
                        // Skip if already added (entry point)
                        if (mod.id === entryPoint.id || nodes.has(mod.id)) return;

                        const modSize = getNodeSize(mod.type, mod.childCount);
                        const enrichedMod: GraphNode = {
                            ...mod,
                            x: 0,
                            y: 0,
                            size: modSize,
                            color: getNodeColor(mod.type),
                            label: getDisplayName(mod.id, mod.name),
                        };

                        nodes.set(mod.id, enrichedMod);

                        if (!graph.hasNode(mod.id)) {
                            graph.addNode(mod.id, {
                                x: 0,
                                y: 0,
                                size: modSize,
                                color: enrichedMod.color,
                                label: enrichedMod.label,
                                nodeType: enrichedMod.type,
                            });
                        }

                        // Group modules by package - connect siblings via __init__.py
                        const parts = mod.id.split('/');
                        if (parts.length > 1) {
                            const parentDir = parts.slice(0, -1).join('/');
                            const parentInitId = `${parentDir}/__init__.py`;

                            // Connect to parent __init__.py if it exists
                            if (graph.hasNode(parentInitId) && mod.id !== parentInitId) {
                                const edgeId = `${parentInitId}->contains->${mod.id}`;
                                try {
                                    if (!graph.hasEdge(edgeId)) {
                                        graph.addEdge(parentInitId, mod.id, {
                                            id: edgeId,
                                            edgeType: 'CONTAINS',
                                        });
                                    }
                                } catch {
                                    // Edge exists
                                }
                            }
                        }
                    });

                    // Apply dagre layout
                    applyDagreLayout(graph);

                    // Update node positions in our map
                    graph.forEachNode((nodeId, attrs) => {
                        const node = nodes.get(nodeId);
                        if (node) {
                            node.x = attrs.x;
                            node.y = attrs.y;
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

            // Expand a node using the new expand API
            expandNode: async (nodeId: string) => {
                const { graph, nodes, expandedNodes, isExpanding } = get();

                if (expandedNodes.has(nodeId) || isExpanding.has(nodeId)) {
                    return;
                }

                const parentNode = nodes.get(nodeId);
                if (!parentNode) {
                    return;
                }

                isExpanding.add(nodeId);
                set({ isExpanding: new Set(isExpanding) });

                try {
                    console.log('[NeuroCode] Expanding node:', parentNode.name);

                    // Use new expand API
                    const { children, outgoing } = await api.expandNode(nodeId);
                    console.log('[NeuroCode] Got', children.length, 'children,', outgoing.length, 'outgoing');

                    // Update parent
                    parentNode.isExpanded = true;
                    if (graph.hasNode(nodeId)) {
                        graph.setNodeAttribute(nodeId, 'size', (parentNode.size || 20) + 6);
                        graph.setNodeAttribute(nodeId, 'color', getNodeColor(parentNode.type, true));
                    }

                    // Add children
                    children.forEach((child) => {
                        if (nodes.has(child.id)) return;

                        const childSize = getNodeSize(child.type, child.childCount);
                        const enrichedChild: GraphNode = {
                            ...child,
                            x: 0,
                            y: 0,
                            size: childSize,
                            color: getNodeColor(child.type),
                            label: getDisplayName(child.id, child.name),
                        };

                        nodes.set(child.id, enrichedChild);

                        if (!graph.hasNode(child.id)) {
                            graph.addNode(child.id, {
                                x: 0,
                                y: 0,
                                size: childSize,
                                color: enrichedChild.color,
                                label: enrichedChild.label,
                                nodeType: enrichedChild.type,
                            });
                        }

                        // Add edge
                        const edgeId = `${nodeId}->${child.id}`;
                        try {
                            if (!graph.hasEdge(edgeId) && !graph.hasEdge(nodeId, child.id)) {
                                graph.addEdge(nodeId, child.id, {
                                    id: edgeId,
                                    edgeType: 'CONTAINS',
                                });
                            }
                        } catch {
                            // Edge already exists
                        }
                    });

                    // Add outgoing connections (CALLS, IMPORTS, etc.)
                    outgoing.forEach((out) => {
                        // Only add if target exists in graph
                        if (!graph.hasNode(out.id)) {
                            // Add as a stub node - cast type to NodeType
                            const nodeType = (out.type || 'unknown') as NodeType;
                            const outSize = getNodeSize(nodeType, 0);
                            const outNode: GraphNode = {
                                id: out.id,
                                name: out.name,
                                type: nodeType,
                                childCount: 0,
                                isExpanded: false,
                                x: 0,
                                y: 0,
                                size: outSize,
                                color: getNodeColor(nodeType),
                                label: getDisplayName(out.id, out.name),
                            };
                            nodes.set(out.id, outNode);
                            graph.addNode(out.id, {
                                x: 0,
                                y: 0,
                                size: outSize,
                                color: outNode.color,
                                label: outNode.label,
                                nodeType: outNode.type,
                            });
                        }

                        // Add edge for the connection
                        const edgeId = `${nodeId}->${out.edgeType}->${out.id}`;
                        try {
                            if (!graph.hasEdge(edgeId)) {
                                graph.addEdge(nodeId, out.id, {
                                    id: edgeId,
                                    edgeType: out.edgeType,
                                });
                            }
                        } catch {
                            // Edge already exists
                        }
                    });

                    // Re-apply dagre layout
                    applyDagreLayout(graph);

                    // Update positions in our map
                    graph.forEachNode((nId, attrs) => {
                        const node = nodes.get(nId);
                        if (node) {
                            node.x = attrs.x;
                            node.y = attrs.y;
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

                // Re-layout
                applyDagreLayout(graph);

                set({
                    nodes: new Map(nodes),
                    expandedNodes: new Set(expandedNodes),
                });
            },

            selectNode: (nodeId: string | null) => {
                set({ selectedNodeId: nodeId });

                if (nodeId) {
                    const nodes = get().nodes;
                    const selectedNode = nodes.get(nodeId);

                    // Build breadcrumbs from hierarchical ID
                    if (selectedNode) {
                        const breadcrumbs: BreadcrumbItem[] = [];
                        const id = selectedNode.id;

                        // Split by :: for nested items
                        if (id.includes('::')) {
                            const [filePath, ...parts] = id.split('::');

                            // Add file as first breadcrumb
                            breadcrumbs.push({
                                id: filePath,
                                name: filePath.split('/').pop()?.replace('.py', '') || filePath,
                                type: 'module' as const,
                            });

                            // Add each nested part
                            let currentId = filePath;
                            parts.forEach((part, index) => {
                                currentId = `${currentId}::${part}`;
                                const partType: NodeType = index === parts.length - 1 ? selectedNode.type : 'class';
                                breadcrumbs.push({
                                    id: currentId,
                                    name: part,
                                    type: partType,
                                });
                            });
                        } else {
                            // Just a file path
                            breadcrumbs.push({
                                id: id,
                                name: selectedNode.name,
                                type: selectedNode.type,
                            });
                        }

                        set({ breadcrumbs });
                    }
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

                // If empty, reset to root view
                if (!nodeId) {
                    get().refresh();
                    return;
                }

                try {
                    // Parse hierarchical ID to get ancestors
                    const parts: string[] = [];
                    if (nodeId.includes('::')) {
                        const [filePath, ...rest] = nodeId.split('::');
                        parts.push(filePath);
                        let current = filePath;
                        for (const part of rest) {
                            current = `${current}::${part}`;
                            parts.push(current);
                        }
                    } else {
                        parts.push(nodeId);
                    }

                    // Expand each ancestor
                    for (const ancestorId of parts.slice(0, -1)) {
                        if (!nodes.has(ancestorId)) {
                            await get().loadEntryPoint();
                        }
                        await expandNode(ancestorId);
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
