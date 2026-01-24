/**
 * NeuroCode Tree Store
 *
 * Zustand store for tree-based graph visualization with lazy loading.
 * Designed for ReactFlow with dagre layout.
 */

import { create } from 'zustand';
import { Node, Edge, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import { api } from '@/services/api';
import { cache } from '@/services/cache';
import { GraphNode, NodeType } from '@/types/graph.types';

// Tree node with visual properties
export interface TreeNode extends GraphNode {
    parentId?: string;
    depth: number;
    x?: number;
    y?: number;
}

// Node colors by type
export const NODE_COLORS: Record<NodeType, string> = {
    package: '#6366f1',   // Indigo
    module: '#8b5cf6',    // Purple
    class: '#10b981',     // Emerald
    function: '#f59e0b',  // Amber
    variable: '#ec4899',  // Pink
    unknown: '#64748b',   // Slate
};

// Edge types
export type EdgeType = 'contains' | 'calls' | 'imports' | 'inherits';

interface TreeState {
    // ReactFlow nodes and edges
    nodes: Node[];
    edges: Edge[];
    
    // Node cache for lazy loading
    nodeCache: Map<string, TreeNode>;
    
    // Expansion state
    expandedIds: Set<string>;
    
    // Selection state
    selectedNodeId: string | null;
    hoveredNodeId: string | null;
    
    // Breadcrumb path
    breadcrumbPath: TreeNode[];
    
    // Loading state
    isLoading: boolean;
    isExpanding: Set<string>;
    error: string | null;
    
    // Search
    searchQuery: string;
    searchResults: GraphNode[];
    
    // Actions
    loadRootNodes: () => Promise<void>;
    expandNode: (nodeId: string) => Promise<void>;
    collapseNode: (nodeId: string) => void;
    toggleNode: (nodeId: string) => Promise<void>;
    selectNode: (nodeId: string | null) => void;
    hoverNode: (nodeId: string | null) => void;
    focusNode: (nodeId: string) => Promise<void>;
    
    // ReactFlow handlers
    onNodesChange: (changes: NodeChange[]) => void;
    onEdgesChange: (changes: EdgeChange[]) => void;
    
    // Search
    setSearchQuery: (query: string) => void;
    search: (query: string) => Promise<void>;
    navigateToSearchResult: (nodeId: string) => Promise<void>;
    
    // Utilities
    getNode: (nodeId: string) => TreeNode | undefined;
    isExpanded: (nodeId: string) => boolean;
    reset: () => void;
}

// Convert API node to TreeNode
function toTreeNode(node: GraphNode, parentId?: string, depth: number = 0): TreeNode {
    return {
        ...node,
        parentId,
        depth,
    };
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

export const useTreeStore = create<TreeState>((set, get) => ({
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

    loadRootNodes: async () => {
        set({ isLoading: true, error: null });
        
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
            
            rootNodes.forEach((node, index) => {
                const treeNode = toTreeNode(node, undefined, 0);
                // Initial grid layout for root nodes
                treeNode.x = (index % 4) * 200;
                treeNode.y = Math.floor(index / 4) * 150;
                newNodeCache.set(node.id, treeNode);
                nodes.push(toReactFlowNode(treeNode, false, false));
            });
            
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
        const { nodeCache, expandedIds, isExpanding, selectedNodeId } = get();
        
        if (expandedIds.has(nodeId) || isExpanding.has(nodeId)) {
            return;
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
            
            // Add children
            result.children.forEach((child, index) => {
                const treeNode = toTreeNode(child, nodeId, parentDepth + 1);
                // Position below parent
                const parentX = parentNode?.x ?? 0;
                const parentY = parentNode?.y ?? 0;
                treeNode.x = parentX + (index - result.children.length / 2) * 150;
                treeNode.y = parentY + 120;
                
                newNodeCache.set(child.id, treeNode);
                newNodes.push(toReactFlowNode(treeNode, false, child.id === selectedNodeId));
                newEdges.push(createEdge(nodeId, child.id, 'contains'));
            });
            
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
        const { expandedIds, nodeCache } = get();
        
        if (!expandedIds.has(nodeId)) {
            return;
        }
        
        // Find all descendants to remove
        const descendantIds = new Set<string>();
        const queue = [nodeId];
        
        while (queue.length > 0) {
            const currentId = queue.shift()!;
            for (const [id, node] of nodeCache) {
                if (node.parentId === currentId && id !== nodeId) {
                    descendantIds.add(id);
                    queue.push(id);
                }
            }
        }
        
        // Remove descendants from cache and nodes
        const newNodeCache = new Map(nodeCache);
        descendantIds.forEach(id => newNodeCache.delete(id));
        
        const newExpandedIds = new Set(expandedIds);
        newExpandedIds.delete(nodeId);
        descendantIds.forEach(id => newExpandedIds.delete(id));
        
        set(state => ({
            nodeCache: newNodeCache,
            nodes: state.nodes.filter(n => !descendantIds.has(n.id)),
            edges: state.edges.filter(e => !descendantIds.has(e.target) && !descendantIds.has(e.source)),
            expandedIds: newExpandedIds,
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
        
        // Update node selection state
        const updatedNodes = get().nodes.map(node => ({
            ...node,
            data: {
                ...node.data,
                isSelected: node.id === nodeId,
            },
        }));
        
        // Build breadcrumb path
        const breadcrumbPath: TreeNode[] = [];
        if (nodeId) {
            let currentNode = nodeCache.get(nodeId);
            while (currentNode) {
                breadcrumbPath.unshift(currentNode);
                currentNode = currentNode.parentId ? nodeCache.get(currentNode.parentId) : undefined;
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

    onNodesChange: (changes: NodeChange[]) => {
        set(state => ({
            nodes: applyNodeChanges(changes, state.nodes),
        }));
    },

    onEdgesChange: (changes: EdgeChange[]) => {
        set(state => ({
            edges: applyEdgeChanges(changes, state.edges),
        }));
    },

    setSearchQuery: (query: string) => {
        set({ searchQuery: query });
    },

    search: async (query: string) => {
        if (!query.trim()) {
            set({ searchResults: [], searchQuery: '' });
            return;
        }
        
        set({ searchQuery: query });
        
        try {
            const response = await api.search(query);
            // Convert SearchResult to GraphNode by adding missing fields
            const results: GraphNode[] = response.results.map(r => ({
                ...r,
                childCount: 0,
                isExpanded: false,
            }));
            set({ searchResults: results });
        } catch (error) {
            console.error('Search failed:', error);
            set({ searchResults: [] });
        }
    },

    navigateToSearchResult: async (nodeId: string) => {
        const { focusNode } = get();
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
}));

export default useTreeStore;
