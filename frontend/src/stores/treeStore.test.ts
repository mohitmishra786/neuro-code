/**
 * TreeStore Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useTreeStore, NODE_COLORS } from './treeStore';

// Mock the API
vi.mock('@/services/api', () => ({
    api: {
        getRootNodes: vi.fn().mockResolvedValue([
            { id: 'pkg1', name: 'package1', type: 'package', childCount: 3 },
            { id: 'mod1', name: 'module1', type: 'module', childCount: 5 },
        ]),
        expandNode: vi.fn().mockResolvedValue({
            children: [
                { id: 'cls1', name: 'Class1', type: 'class', childCount: 2 },
                { id: 'fn1', name: 'function1', type: 'function', childCount: 0 },
            ],
            outgoing: [],
        }),
        search: vi.fn().mockResolvedValue({
            results: [
                { id: 'cls1', name: 'Class1', type: 'class' },
            ],
        }),
        getNodeAncestors: vi.fn().mockResolvedValue([]),
    },
}));

// Mock the cache
vi.mock('@/services/cache', () => ({
    cache: {
        init: vi.fn().mockResolvedValue(undefined),
        getChildren: vi.fn().mockResolvedValue(null),
        setChildren: vi.fn().mockResolvedValue(undefined),
        setNodes: vi.fn().mockResolvedValue(undefined),
        clear: vi.fn().mockResolvedValue(undefined),
    },
}));

describe('useTreeStore', () => {
    beforeEach(() => {
        // Reset the store before each test
        useTreeStore.getState().reset();
    });

    describe('NODE_COLORS', () => {
        it('should have colors for all node types', () => {
            expect(NODE_COLORS.package).toBeDefined();
            expect(NODE_COLORS.module).toBeDefined();
            expect(NODE_COLORS.class).toBeDefined();
            expect(NODE_COLORS.function).toBeDefined();
            expect(NODE_COLORS.variable).toBeDefined();
            expect(NODE_COLORS.unknown).toBeDefined();
        });
    });

    describe('loadRootNodes', () => {
        it('should set loading state while fetching', async () => {
            const { loadRootNodes } = useTreeStore.getState();
            
            const loadPromise = loadRootNodes();
            expect(useTreeStore.getState().isLoading).toBe(true);
            
            await loadPromise;
            expect(useTreeStore.getState().isLoading).toBe(false);
        });

        it('should populate nodes after loading', async () => {
            await useTreeStore.getState().loadRootNodes();
            
            const { nodes, nodeCache } = useTreeStore.getState();
            expect(nodes.length).toBe(2);
            expect(nodeCache.size).toBe(2);
        });
    });

    describe('expandNode', () => {
        it('should not expand if already expanded', async () => {
            const store = useTreeStore.getState();
            await store.loadRootNodes();
            
            // Expand a node
            await store.expandNode('pkg1');
            const nodesAfterFirstExpand = useTreeStore.getState().nodes.length;
            
            // Try to expand again - should not add more nodes
            await store.expandNode('pkg1');
            expect(useTreeStore.getState().nodes.length).toBe(nodesAfterFirstExpand);
        });

        it('should add children to nodes and edges', async () => {
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            const { nodes, edges, expandedIds } = useTreeStore.getState();
            
            // Should have 2 root nodes + 2 children
            expect(nodes.length).toBe(4);
            // Should have 2 edges (from pkg1 to children)
            expect(edges.length).toBe(2);
            // pkg1 should be marked as expanded
            expect(expandedIds.has('pkg1')).toBe(true);
        });
    });

    describe('collapseNode', () => {
        it('should remove children when collapsed', async () => {
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            // Collapse the node
            useTreeStore.getState().collapseNode('pkg1');
            
            const { nodes, edges, expandedIds } = useTreeStore.getState();
            
            // Should have only 2 root nodes
            expect(nodes.length).toBe(2);
            expect(edges.length).toBe(0);
            expect(expandedIds.has('pkg1')).toBe(false);
        });
    });

    describe('toggleNode', () => {
        it('should expand when collapsed', async () => {
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().toggleNode('pkg1');
            
            expect(useTreeStore.getState().expandedIds.has('pkg1')).toBe(true);
        });

        it('should collapse when expanded', async () => {
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            useTreeStore.getState().toggleNode('pkg1');
            
            expect(useTreeStore.getState().expandedIds.has('pkg1')).toBe(false);
        });
    });

    describe('selectNode', () => {
        it('should update selectedNodeId', async () => {
            await useTreeStore.getState().loadRootNodes();
            
            useTreeStore.getState().selectNode('pkg1');
            
            expect(useTreeStore.getState().selectedNodeId).toBe('pkg1');
        });

        it('should build breadcrumb path', async () => {
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            useTreeStore.getState().selectNode('cls1');
            
            const { breadcrumbPath } = useTreeStore.getState();
            // Should have pkg1 -> cls1
            expect(breadcrumbPath.length).toBe(2);
            expect(breadcrumbPath[0].id).toBe('pkg1');
            expect(breadcrumbPath[1].id).toBe('cls1');
        });
    });

    describe('reset', () => {
        it('should clear all state', async () => {
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            useTreeStore.getState().reset();
            
            const state = useTreeStore.getState();
            expect(state.nodes.length).toBe(0);
            expect(state.edges.length).toBe(0);
            expect(state.nodeCache.size).toBe(0);
            expect(state.expandedIds.size).toBe(0);
            expect(state.selectedNodeId).toBe(null);
        });
    });

    describe('search', () => {
        it('should update search results', async () => {
            await useTreeStore.getState().search('Class');
            
            const { searchResults, searchQuery } = useTreeStore.getState();
            expect(searchQuery).toBe('Class');
            expect(searchResults.length).toBe(1);
        });

        it('should clear results for empty query', async () => {
            await useTreeStore.getState().search('Class');
            await useTreeStore.getState().search('');
            
            const { searchResults, searchQuery } = useTreeStore.getState();
            expect(searchQuery).toBe('');
            expect(searchResults.length).toBe(0);
        });
    });

    describe('isExpanded', () => {
        it('should return true for expanded nodes', async () => {
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            expect(useTreeStore.getState().isExpanded('pkg1')).toBe(true);
        });

        it('should return false for non-expanded nodes', async () => {
            await useTreeStore.getState().loadRootNodes();
            
            expect(useTreeStore.getState().isExpanded('pkg1')).toBe(false);
        });
    });

    describe('getNode', () => {
        it('should return node from cache', async () => {
            await useTreeStore.getState().loadRootNodes();
            
            const node = useTreeStore.getState().getNode('pkg1');
            expect(node).toBeDefined();
            expect(node?.name).toBe('package1');
        });

        it('should return undefined for non-existent nodes', () => {
            const node = useTreeStore.getState().getNode('nonexistent');
            expect(node).toBeUndefined();
        });
    });
});
