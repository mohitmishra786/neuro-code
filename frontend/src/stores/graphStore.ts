import { create } from 'zustand';
import {
    Node,
    Edge,
    OnNodesChange,
    OnEdgesChange,
    applyNodeChanges,
    applyEdgeChanges,
    NodeChange,
    EdgeChange,
} from 'reactflow';
import { api } from '@/services/api';
import { ProjectTreeNode } from '@/types/graph.types';

interface GraphState {
    nodes: Node[];
    edges: Edge[];
    tree: ProjectTreeNode | null;
    loading: boolean;
    error: string | null;

    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;
    setNodes: (nodes: Node[]) => void;
    setEdges: (edges: Edge[]) => void;

    loadProjectTree: (path: string) => Promise<void>;
    expandNode: (nodeId: string) => void;
    collapseNode: (nodeId: string) => void;

    searchQuery: string;
    searchResults: any[];
    setSearchQuery: (query: string) => void;
    searchNodes: (query: string) => Promise<void>;
    focusNode: (nodeId: string) => void;
}

// Convert tree to React Flow nodes/edges (basic initial layout)
const processTree = (tree: ProjectTreeNode): { nodes: Node[]; edges: Edge[] } => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Basic layout settings
    let yOffset = 0;
    const X_OFFSET = 50;
    const NODE_HEIGHT = 60;
    const NODE_WIDTH = 250;

    // Flatten the top-level children for the initial view
    // We can also use a recursive function if we want to show everything initially, 
    // but "Top Level: The UI should initially only show the Building Blocks"

    if (tree.children) {
        tree.children.forEach((child, index) => {
            nodes.push({
                id: child.id,
                type: 'module', // We will map 'package'/'module' to a generic custom node or specific ones
                position: { x: X_OFFSET, y: yOffset },
                data: {
                    label: child.label || child.id,
                    original: child,
                    isExpanded: false
                },
            });
            yOffset += NODE_HEIGHT + 20;
        });
    }

    return { nodes, edges };
};

export const useGraphStore = create<GraphState>((set, get) => ({
    nodes: [],
    edges: [],
    tree: null,
    loading: false,
    error: null,

    onNodesChange: (changes: NodeChange[]) => {
        set({
            nodes: applyNodeChanges(changes, get().nodes),
        });
    },
    onEdgesChange: (changes: EdgeChange[]) => {
        set({
            edges: applyEdgeChanges(changes, get().edges),
        });
    },
    setNodes: (nodes) => set({ nodes }),
    setEdges: (edges) => set({ edges }),

    loadProjectTree: async (path: string) => {
        set({ loading: true, error: null });
        try {
            const tree = await api.getProjectTree(path);
            const { nodes, edges } = processTree(tree);
            set({ tree, nodes, edges, loading: false });
        } catch (err: any) {
            set({ error: err.message || 'Failed to load tree', loading: false });
        }
    },

    expandNode: (nodeId: string) => {
        const { nodes, tree } = get();
        if (!tree) return;

        // Helper to find node in tree
        const findNode = (root: ProjectTreeNode, id: string): ProjectTreeNode | null => {
            if (root.id === id) return root;
            if (root.children) {
                for (const child of root.children) {
                    const found = findNode(child, id);
                    if (found) return found;
                }
            }
            return null;
        };

        const treeNode = findNode(tree, nodeId);
        if (!treeNode || !treeNode.children || treeNode.children.length === 0) return;

        // Check if children are already added
        const childrenIds = new Set(treeNode.children.map(c => c.id));
        if (nodes.some(n => childrenIds.has(n.id))) return;

        // Update parent node (make it a group)
        set({
            nodes: nodes.map(n =>
                n.id === nodeId
                    ? {
                        ...n,
                        style: { ...n.style, width: 600, height: 400, backgroundColor: 'rgba(0,0,0,0.2)' }, // Expand visual area
                        data: { ...n.data, isExpanded: true }
                    }
                    : n
            )
        });

        // Add children nodes
        const newNodes: Node[] = [];
        let yOffset = 20; // local relative offset
        const xOffset = 20;

        treeNode.children.forEach(child => {
            newNodes.push({
                id: child.id,
                type: child.type === 'package' || child.type === 'module' ? 'module' : 'default',
                position: { x: xOffset, y: yOffset },
                parentNode: nodeId,
                extent: 'parent', // Constrain to parent bounds? optional
                data: {
                    label: child.label || child.id,
                    original: child,
                    isExpanded: false
                },
                style: { width: 550, height: 60 }
            });
            yOffset += 80;
        });

        set(state => ({
            nodes: [...state.nodes, ...newNodes]
        }));
    },

    collapseNode: (nodeId: string) => {
        // Basic collapse
        const { nodes, edges } = get();
        const descendants = new Set<string>();

        const findDescendants = (id: string) => {
            edges.forEach(e => {
                if (e.source === id) {
                    descendants.add(e.target);
                    findDescendants(e.target);
                }
            });
        };

        findDescendants(nodeId);

        set({
            nodes: nodes.filter(n => !descendants.has(n.id)),
            edges: edges.filter(e => e.source !== nodeId && !descendants.has(e.target)) // Remove outgoing edges from descendants? 
            // Actually edges are auto-cleanup if nodes removed usually, but here manually
        });
    },

    // Search state
    searchQuery: '',
    searchResults: [],
    setSearchQuery: (query: string) => set({ searchQuery: query }),
    searchNodes: async (query: string) => {
        set({ searchQuery: query });
        if (!query.trim()) {
            set({ searchResults: [] });
            return;
        }
        try {
            const res = await api.search(query);
            set({ searchResults: res.results });
        } catch (err) {
            console.error(err);
        }
    },

    focusNode: (nodeId: string) => {
        const { expandNode, tree } = get();
        if (!tree) return;

        // Find path to node
        const path: string[] = [];
        const findPath = (root: ProjectTreeNode, targetId: string, currentPath: string[]): boolean => {
            if (root.id === targetId) {
                path.push(...currentPath);
                return true;
            }
            if (root.children) {
                for (const child of root.children) {
                    if (findPath(child, targetId, [...currentPath, root.id])) return true;
                }
            }
            return false;
        };

        // We search from roots (or if tree is root)
        findPath(tree, nodeId, []);

        // Expand all along path
        path.forEach(pid => {
            if (pid !== 'root') expandNode(pid);
        });

        // Select/Highlight node (optional)
        // For now just expanding path reveals it
    }
}));
