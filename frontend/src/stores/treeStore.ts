/**
 * NeuroCode Tree Store
 *
 * Zustand store for tree-based graph visualization with lazy loading.
 * Designed for ReactFlow with dagre layout.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Node, Edge, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import { api } from '@/services/api';
import { cache } from '@/services/cache';
import { GraphNode, NodeType, EdgeType } from '@/types/graph.types';

// Tree node with visual properties
export interface TreeNode extends GraphNode {
    parentId?: string;
    depth: number;
    x?: number;
    y?: number;
}

// Serializable node cache entry
interface NodeCacheEntry {
    node: TreeNode;
    timestamp: number;
}

// Build parent-to-children mapping for efficient descendant lookups
function buildParentMap(nodeCache: ReadonlyMap<string, TreeNode>): Map<string, string[]> {
    const parentMap = new Map<string, string[]>();
    for (const [, node] of nodeCache) {
        if (node.parentId) {
            const children = parentMap.get(node.parentId) ?? [];
            children.push(node.id);
            parentMap.set(node.parentId, children);
        }
    }
    return parentMap;
}

// Find all descendants using parent-to-children mapping (O(D) instead of O(D*C))
function findDescendants(nodeId: string, parentMap: Map<string, string[]>): Set<string> {
    const descendants = new Set<string>();
    const queue = [nodeId];

    while (queue.length > 0) {
        const currentId = queue.shift()!;
        const children = parentMap.get(currentId) ?? [];

        for (const childId of children) {
            if (!descendants.has(childId)) {
                descendants.add(childId);
                queue.push(childId);
            }
        }
    }

    return descendants;
}

// Expansion attempt tracking for infinite loop prevention
const expansionAttempts = new Map<string, number>();
const MAX_EXPANSION_ATTEMPTS = 3;
const EXPANSION_COOLDOWN_MS = 5000;

// Search request tracking for race condition prevention
let searchRequestId = 0;
let currentSearchId = 0;

// Node colors by type
export const NODE_COLORS: Record<NodeType, string> = {
    package: '#6366f1',   // Indigo
    module: '#8b5cf6',    // Purple
    class: '#10b981',     // Emerald
    function: '#f59e0b',  // Amber
    variable: '#ec4899',  // Pink
    unknown: '#64748b',   // Slate
};

interface TreeState {
    /**
     * ReactFlow nodes for rendering the graph visualization.
     */
    readonly nodes: readonly Node[];

    /**
     * ReactFlow edges representing relationships between nodes.
     */
    readonly edges: readonly Edge[];

    /**
     * Local cache of all loaded tree nodes, keyed by node ID.
     * Used for efficient node lookups and lazy loading.
     */
    readonly nodeCache: ReadonlyMap<string, TreeNode>;

    /**
     * Set of node IDs that have been expanded to show children.
     */
    readonly expandedIds: ReadonlySet<string>;

    /**
     * Currently selected node ID, or null if no selection.
     */
    readonly selectedNodeId: string | null;

    /**
     * Currently hovered node ID, or null if no hover.
     */
    readonly hoveredNodeId: string | null;

    /**
     * Array of nodes forming the breadcrumb path from root to selected node.
     */
    readonly breadcrumbPath: readonly TreeNode[];

    /**
     * Whether the store is currently loading data.
     */
    readonly isLoading: boolean;

    /**
     * Set of node IDs currently being expanded (for loading indicators).
     */
    readonly isExpanding: ReadonlySet<string>;

    /**
     * Error message if an error occurred, or null if no error.
     */
    readonly error: string | null;

    /**
     * Whether the browser is online and network requests can be made.
     */
    readonly isOnline: boolean;

    /**
     * Current search query text.
     */
    readonly searchQuery: string;

    /**
     * Array of search results matching the current query.
     */
    readonly searchResults: readonly GraphNode[];

    /**
     * Load root nodes from cache or API.
     * Initializes the node cache and sets up the initial graph state.
     */
    readonly loadRootNodes: () => Promise<void>;

    /**
     * Expand a node to load and display its children.
     * @param nodeId - The ID of the node to expand
     */
    readonly expandNode: (nodeId: string) => Promise<void>;

    /**
     * Collapse a node, hiding its children and descendants.
     * @param nodeId - The ID of the node to collapse
     */
    readonly collapseNode: (nodeId: string) => void;

    /**
     * Toggle the expanded state of a node.
     * @param nodeId - The ID of the node to toggle
     */
    readonly toggleNode: (nodeId: string) => Promise<void>;

    /**
     * Select a node, updating the breadcrumb path.
     * @param nodeId - The ID of the node to select, or null to deselect
     */
    readonly selectNode: (nodeId: string | null) => void;

    /**
     * Set the currently hovered node.
     * @param nodeId - The ID of the node being hovered, or null to clear
     */
    readonly hoverNode: (nodeId: string | null) => void;

    /**
     * Focus on a specific node by loading its ancestors and expanding the path.
     * @param nodeId - The ID of the node to focus on
     */
    readonly focusNode: (nodeId: string) => Promise<void>;

    /**
     * Handle changes to ReactFlow nodes (selection, expansion, etc.).
     * @param changes - Array of node changes from ReactFlow
     */
    readonly onNodesChange: (changes: readonly NodeChange[]) => void;

    /**
     * Handle changes to ReactFlow edges.
     * @param changes - Array of edge changes from ReactFlow
     */
    readonly onEdgesChange: (changes: readonly EdgeChange[]) => void;

    /**
     * Set the current search query.
     * @param query - The search query string
     */
    readonly setSearchQuery: (query: string) => void;

    /**
     * Perform a search for nodes matching the query.
     * @param query - The search query string
     */
    readonly search: (query: string) => Promise<void>;

    /**
     * Navigate to a search result and clear the search.
     * @param nodeId - The ID of the node to navigate to
     */
    readonly navigateToSearchResult: (nodeId: string) => Promise<void>;

    /**
     * Get a node from the cache by ID.
     * @param nodeId - The ID of the node to retrieve
     * @returns The tree node, or undefined if not found
     */
    readonly getNode: (nodeId: string) => TreeNode | undefined;

    /**
     * Check if a node is currently expanded.
     * @param nodeId - The ID of the node to check
     * @returns True if the node is expanded
     */
    readonly isExpanded: (nodeId: string) => boolean;

    /**
     * Reset the store to its initial state, clearing all data.
     */
    readonly reset: () => void;
}

// Convert API node to TreeNode
function toTreeNode(node: GraphNode, parentId?: string, depth: number = 0): TreeNode {
    return {
        ...node,
        parentId,
        depth,
    };
}

// Unique ID generator for cases where backend may return duplicates
let idCounter = 0;
function generateUniqueId(baseId: string): string {
    return `${baseId}_${++idCounter}`;
}

// Check if ID already exists in cache
function isIdUnique(id: string, nodeCache: ReadonlyMap<string, TreeNode>): boolean {
    return !nodeCache.has(id);
}

// Convert TreeNode to ReactFlow Node
function toReactFlowNode(node: TreeNode, isExpanded: boolean, isSelected: boolean): Node {
    return {
        id: node.id,
        type: 'circleNode', // Custom node type
        position: { x: node.x || 0, y: node.y || 0 },
        data: {
            label: node.name,
            nodeType: node.type,
            childCount: node.childCount,
            isExpanded,
            isSelected,
            qualifiedName: node.qualifiedName,
            docstring: node.docstring,
            isAsync: node.isAsync,
            complexity: node.complexity,
        },
    };
}

// Create edge between nodes
function createEdge(sourceId: string, targetId: string, edgeType: EdgeType = 'contains'): Edge {
    const edgeColor = edgeType === 'contains' ? '#64748b' : 
                      edgeType === 'calls' ? '#f59e0b' :
                      edgeType === 'imports' ? '#6366f1' : '#10b981';
    return {
        id: `${sourceId}->${targetId}`,
        source: sourceId,
        target: targetId,
        type: 'smoothstep',
        animated: edgeType === 'calls',
        style: {
            stroke: edgeColor,
            strokeWidth: edgeType === 'contains' ? 2 : 1.5,
            strokeDasharray: edgeType === 'imports' ? '5,5' : undefined,
        },
        markerEnd: {
            type: 'arrowclosed',
            color: edgeColor,
        } as Edge['markerEnd'],
        data: { edgeType },
    };
}

export const useTreeStore = create<TreeState>()(
    persist(
        (set, get) => ({
            nodes: [],
            edges: [],
            nodeCache: new Map(),
            expandedIds: new Set(),
            selectedNodeId: null,
            hoveredNodeId: null,
            breadcrumbPath: [],
            isLoading: false,
            isExpanding: new Set(),
            error: null,
            searchQuery: '',
            searchResults: [],
            isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,

    loadRootNodes: async () => {
        // Check online status before making network requests
        if (typeof navigator !== 'undefined' && !navigator.onLine) {
            set({ 
                isLoading: false, 
                error: 'You are offline. Some features may be unavailable.',
                isOnline: false,
            });
            return;
        }

        set({ isLoading: true, error: null, isOnline: true });
        
        try {
            // Initialize cache
            await cache.init();
            
            // Try to get cached root nodes first
            let rootNodes = await cache.getChildren('__root__');
            
            if (!rootNodes) {
                // Fetch from API if not cached
                rootNodes = await api.getRootNodes();
                // Cache the root nodes
                await cache.setChildren('__root__', rootNodes);
                await cache.setNodes(rootNodes);
            }
            
            const newNodeCache = new Map<string, TreeNode>();
            const nodes: Node[] = [];
            const seenIds = new Set<string>();
            const duplicateIds: string[] = [];
            
            rootNodes.forEach((node, index) => {
                let nodeId = node.id;
                
                // Check for duplicate ID
                if (!isIdUnique(nodeId, newNodeCache)) {
                    if (!seenIds.has(nodeId)) {
                        duplicateIds.push(nodeId);
                    }
                    nodeId = generateUniqueId(node.id);
                }
                
                const treeNode = toTreeNode({ ...node, id: nodeId }, undefined, 0);
                // Initial grid layout for root nodes
                treeNode.x = (index % 4) * 200;
                treeNode.y = Math.floor(index / 4) * 150;
                newNodeCache.set(nodeId, treeNode);
                nodes.push(toReactFlowNode(treeNode, false, false));
                seenIds.add(nodeId);
            });
            
            // Log duplicates for debugging
            if (duplicateIds.length > 0) {
                console.warn('[TreeStore] Duplicate root node IDs detected and fixed:', duplicateIds);
            }
            
            set({
                nodeCache: newNodeCache,
                nodes,
                edges: [],
                isLoading: false,
            });
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to load root nodes',
                isLoading: false,
            });
        }
    },

    expandNode: async (nodeId: string) => {
        const { nodeCache, expandedIds, isExpanding, isOnline, selectedNodeId } = get();

        // Prevent infinite expansion loops
        const now = Date.now();
        const lastAttempt = expansionAttempts.get(nodeId) ?? 0;
        if (now - lastAttempt < EXPANSION_COOLDOWN_MS) {
            const attempts = expansionAttempts.get(nodeId) ?? 0;
            if (attempts >= MAX_EXPANSION_ATTEMPTS) {
                console.warn(`[TreeStore] Expansion blocked for ${nodeId} - too many attempts`);
                return;
            }
        }
        expansionAttempts.set(nodeId, (expansionAttempts.get(nodeId) ?? 0) + 1);

        if (expandedIds.has(nodeId) || isExpanding.has(nodeId)) {
            return;
        }

        // Check online status before making network requests
        if (typeof navigator !== 'undefined' && !navigator.onLine) {
            const cachedChildren = await cache.getChildren(nodeId);
            if (cachedChildren && cachedChildren.length > 0) {
                set({ isOnline: false, error: 'You are offline. Using cached data.' });
            } else {
                set({
                    isOnline: false,
                    error: 'You are offline and this data is not cached.',
                    isExpanding: new Set([...isExpanding].filter(id => id !== nodeId)),
                });
                return;
            }
        }
        
        // Mark as expanding
        set({ isExpanding: new Set([...isExpanding, nodeId]) });
        
        try {
            // Try to get cached children first
            let cachedChildren = await cache.getChildren(nodeId);
            let result: { children: GraphNode[]; outgoing: Array<{ id: string; edgeType: string }> };
            
            if (cachedChildren && cachedChildren.length > 0) {
                // Use cached data
                result = { children: cachedChildren, outgoing: [] };
            } else {
                // Fetch from API
                result = await api.expandNode(nodeId);
                
                // Cache the children
                if (result.children.length > 0) {
                    await cache.setChildren(nodeId, result.children);
                    await cache.setNodes(result.children);
                }
            }
            
            const parentNode = nodeCache.get(nodeId);
            const parentDepth = parentNode?.depth ?? 0;
            
            if (!result.children.length && !result.outgoing.length) {
                // No children, just mark as expanded
                set(state => ({
                    expandedIds: new Set([...state.expandedIds, nodeId]),
                    isExpanding: new Set([...state.isExpanding].filter(id => id !== nodeId)),
                }));
                return;
            }
            
            const newNodeCache = new Map(nodeCache);
            const newNodes: Node[] = [];
            const newEdges: Edge[] = [];
            
            // Track seen IDs to detect duplicates
            const seenIds = new Set<string>();
            const duplicateIds: string[] = [];

            // Add children
            result.children.forEach((child, index) => {
                let nodeId = child.id;
                
                // Check for duplicate ID
                if (!isIdUnique(nodeId, newNodeCache)) {
                    if (!seenIds.has(nodeId)) {
                        duplicateIds.push(nodeId);
                    }
                    // Generate unique ID
                    nodeId = generateUniqueId(child.id);
                }
                
                const treeNode = toTreeNode({ ...child, id: nodeId }, nodeId, parentDepth + 1);
                // Position below parent
                const parentX = parentNode?.x ?? 0;
                const parentY = parentNode?.y ?? 0;
                treeNode.x = parentX + (index - result.children.length / 2) * 150;
                treeNode.y = parentY + 120;
                
                newNodeCache.set(nodeId, treeNode);
                newNodes.push(toReactFlowNode(treeNode, false, nodeId === selectedNodeId));
                newEdges.push(createEdge(nodeId, nodeId, 'contains'));
                seenIds.add(nodeId);
            });
            
            // Log duplicates for debugging
            if (duplicateIds.length > 0) {
                console.warn('[TreeStore] Duplicate node IDs detected and fixed:', duplicateIds);
            }
            
            // Add outgoing connections (calls, imports, inherits)
            result.outgoing.forEach((connection) => {
                // Only add edge if target exists in cache
                if (newNodeCache.has(connection.id) || nodeCache.has(connection.id)) {
                    const edgeType = connection.edgeType.toLowerCase() as EdgeType;
                    newEdges.push(createEdge(nodeId, connection.id, edgeType));
                }
            });
            
            set(state => ({
                nodeCache: newNodeCache,
                nodes: [...state.nodes, ...newNodes],
                edges: [...state.edges, ...newEdges],
                expandedIds: new Set([...state.expandedIds, nodeId]),
                isExpanding: new Set([...state.isExpanding].filter(id => id !== nodeId)),
            }));
            
        } catch (error) {
            set(state => ({
                error: error instanceof Error ? error.message : 'Failed to expand node',
                isExpanding: new Set([...state.isExpanding].filter(id => id !== nodeId)),
            }));
        }
    },

    collapseNode: (nodeId: string) => {
        const { expandedIds, nodeCache, selectedNodeId } = get();
        
        if (!expandedIds.has(nodeId)) {
            return;
        }
        
        // Build parent-to-children mapping for efficient descendant lookup
        const parentMap = buildParentMap(nodeCache);
        
        // Find descendants using efficient O(D) algorithm
        const descendantIds = findDescendants(nodeId, parentMap);
        
        // Remove descendants from cache and nodes
        const newNodeCache = new Map(nodeCache);
        descendantIds.forEach(id => newNodeCache.delete(id));
        
        const newExpandedIds = new Set(expandedIds);
        newExpandedIds.delete(nodeId);
        descendantIds.forEach(id => newExpandedIds.delete(id));
        
        // Clear selectedNodeId if the selected node is being removed
        const shouldClearSelection = selectedNodeId !== null && descendantIds.has(selectedNodeId);
        
        set(state => ({
            nodeCache: newNodeCache,
            nodes: state.nodes.filter(n => !descendantIds.has(n.id)),
            edges: state.edges.filter(e => !descendantIds.has(e.target) && !descendantIds.has(e.source)),
            expandedIds: newExpandedIds,
            selectedNodeId: shouldClearSelection ? null : state.selectedNodeId,
        }));
    },

    toggleNode: async (nodeId: string) => {
        const { expandedIds, expandNode, collapseNode } = get();
        if (expandedIds.has(nodeId)) {
            collapseNode(nodeId);
        } else {
            await expandNode(nodeId);
        }
    },

    selectNode: (nodeId: string | null) => {
        const { nodeCache } = get();
        
        // Validate that the node exists if not null
        if (nodeId !== null && !nodeCache.has(nodeId)) {
            console.warn('[TreeStore] Attempted to select non-existent node:', nodeId);
            set({ selectedNodeId: null });
            return;
        }
        
        // Update node selection state
        const updatedNodes = get().nodes.map(node => ({
            ...node,
            data: {
                ...node.data,
                isSelected: node.id === nodeId,
            },
        }));
        
        // Build breadcrumb path - with safety checks
        const breadcrumbPath: TreeNode[] = [];
        if (nodeId) {
            const visitedIds = new Set<string>();
            let currentNode = nodeCache.get(nodeId);
            
            while (currentNode) {
                // Prevent infinite loops from circular references
                if (visitedIds.has(currentNode.id)) {
                    console.warn('[TreeStore] Circular reference detected in breadcrumb path');
                    break;
                }
                visitedIds.add(currentNode.id);
                
                breadcrumbPath.unshift(currentNode);
                
                // Safety check for deeply nested paths
                if (breadcrumbPath.length > 1000) {
                    console.warn('[TreeStore] Breadcrumb path exceeds maximum depth');
                    break;
                }
                
                if (!currentNode.parentId) break;
                currentNode = nodeCache.get(currentNode.parentId);
            }
        }
        
        set({
            selectedNodeId: nodeId,
            nodes: updatedNodes,
            breadcrumbPath,
        });
    },

    hoverNode: (nodeId: string | null) => {
        set({ hoveredNodeId: nodeId });
    },

    focusNode: async (nodeId: string) => {
        const { nodeCache, expandNode, selectNode } = get();
        
        // If node is already in cache, just select it
        if (nodeCache.has(nodeId)) {
            selectNode(nodeId);
            return;
        }
        
        // Otherwise, try to load the path to this node
        try {
            const ancestors = await api.getNodeAncestors(nodeId);
            
            // Expand each ancestor in order
            for (const ancestor of ancestors) {
                if (!nodeCache.has(ancestor.id)) {
                    // Node not loaded yet, expand its parent
                    const parentNode = ancestors.find(a => 
                        nodeCache.get(ancestor.id)?.parentId === a.id
                    );
                    if (parentNode) {
                        await expandNode(parentNode.id);
                    }
                }
            }
            
            // Finally, expand the direct parent and select the node
            const directParent = ancestors[ancestors.length - 1];
            if (directParent) {
                await expandNode(directParent.id);
            }
            
            selectNode(nodeId);
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to focus node',
            });
        }
    },

    onNodesChange: (changes: readonly NodeChange[]) => {
        set(state => ({
            nodes: applyNodeChanges([...changes], state.nodes),
        }));
    },

    onEdgesChange: (changes: readonly EdgeChange[]) => {
        set(state => ({
            edges: applyEdgeChanges([...changes], state.edges),
        }));
    },

    setSearchQuery: (query: string) => {
        set({ searchQuery: query });
    },

    search: async (query: string) => {
        const currentRequestId = ++searchRequestId;
        
        if (!query.trim()) {
            // Only clear if this is the latest request
            if (currentRequestId === searchRequestId) {
                set({ searchResults: [], searchQuery: '' });
            }
            return;
        }
        
        // Check online status for search requests
        if (typeof navigator !== 'undefined' && !navigator.onLine) {
            set({ 
                searchQuery: query,
                error: 'You are offline. Search results may be outdated.',
            });
            return;
        }
        
        set({ searchQuery: query });
        
        try {
            const response = await api.search(query);
            
            // Only update if this is still the latest request
            if (currentRequestId !== searchRequestId) {
                return;
            }
            
            // Convert SearchResult to GraphNode by adding missing fields
            const results: GraphNode[] = response.results.map(r => ({
                ...r,
                childCount: 0,
                isExpanded: false,
            }));
            set({ searchResults: results });
        } catch (error) {
            // Only handle error if this is still the latest request
            if (currentRequestId !== searchRequestId) {
                return;
            }
            
            console.error('Search failed:', error);
            set({ searchResults: [] });
        }
    },

    navigateToSearchResult: async (nodeId: string) => {
        const { focusNode } = get();
        
        // Cancel any pending search navigation by incrementing the search ID
        ++currentSearchId;
        ++searchRequestId;
        
        await focusNode(nodeId);
        set({ searchQuery: '', searchResults: [] });
    },

    getNode: (nodeId: string) => {
        return get().nodeCache.get(nodeId);
    },

    isExpanded: (nodeId: string) => {
        return get().expandedIds.has(nodeId);
    },

    reset: () => {
        // Clear local cache as well
        cache.clear().catch(console.error);
        
        set({
            nodes: [],
            edges: [],
            nodeCache: new Map(),
            expandedIds: new Set(),
            selectedNodeId: null,
            hoveredNodeId: null,
            breadcrumbPath: [],
            isLoading: false,
            isExpanding: new Set(),
            error: null,
            searchQuery: '',
            searchResults: [],
        });
    },
}), {
    name: 'neurocode-tree-store',
    storage: createJSONStorage(() => localStorage),
    partialize: (state) => ({
        expandedIds: Array.from(state.expandedIds),
        selectedNodeId: state.selectedNodeId,
        breadcrumbPath: state.breadcrumbPath.map(node => ({
            id: node.id,
            name: node.name,
            type: node.type,
            qualifiedName: node.qualifiedName,
            parentId: node.parentId,
            depth: node.depth,
            childCount: node.childCount,
            isExpanded: node.isExpanded,
        })),
    }),
    merge: (persisted: Partial<TreeState> | undefined, current: TreeState): TreeState => {
        const merged = { ...current, ...persisted };

        if (persisted?.expandedIds && Array.isArray(persisted.expandedIds)) {
            merged.expandedIds = new Set(persisted.expandedIds);
        }

        if (persisted?.breadcrumbPath && Array.isArray(persisted.breadcrumbPath)) {
            merged.breadcrumbPath = persisted.breadcrumbPath;
        }

        return merged;
    },
}));

// Online/offline event listeners
if (typeof window !== 'undefined') {
    window.addEventListener('online', () => {
        useTreeStore.setState({ isOnline: true, error: null });
    });
    
    window.addEventListener('offline', () => {
        useTreeStore.setState({ isOnline: false, error: 'You have gone offline. Changes will be synced when connection is restored.' });
    });
}

export default useTreeStore;
