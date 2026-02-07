/**
 * TreeStore Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useTreeStore, NODE_COLORS } from './treeStore';
import { isValidNodeType, isValidEdgeType } from '@/types/graph.types';

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

    describe('isValidNodeType', () => {
        it('should validate correct node types', () => {
            expect(isValidNodeType('package')).toBe(true);
            expect(isValidNodeType('module')).toBe(true);
            expect(isValidNodeType('class')).toBe(true);
            expect(isValidNodeType('function')).toBe(true);
            expect(isValidNodeType('variable')).toBe(true);
            expect(isValidNodeType('unknown')).toBe(true);
        });

        it('should reject invalid node types', () => {
            expect(isValidNodeType('invalid')).toBe(false);
            expect(isValidNodeType('')).toBe(false);
            expect(isValidNodeType(123 as unknown)).toBe(false);
            expect(isValidNodeType(null)).toBe(false);
            expect(isValidNodeType(undefined)).toBe(false);
            expect(isValidNodeType({}) as unknown).toBe(false);
        });
    });

    describe('isValidEdgeType', () => {
        it('should validate correct edge types', () => {
            expect(isValidEdgeType('contains')).toBe(true);
            expect(isValidEdgeType('calls')).toBe(true);
            expect(isValidEdgeType('imports')).toBe(true);
            expect(isValidEdgeType('inherits')).toBe(true);
        });

        it('should reject invalid edge types', () => {
            expect(isValidEdgeType('invalid')).toBe(false);
            expect(isValidEdgeType('')).toBe(false);
            expect(isValidEdgeType(123 as unknown)).toBe(false);
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

    describe('duplicate node ID handling', () => {
        it('should generate unique IDs when duplicates are detected in root nodes', async () => {
            useTreeStore.getState().reset();
            
            const { api } = await import('@/services/api');
            vi.mocked(api.getRootNodes).mockResolvedValue([
                { id: 'duplicate', name: 'node1', type: 'class' as const, childCount: 1, isExpanded: false },
                { id: 'duplicate', name: 'node2', type: 'class' as const, childCount: 1, isExpanded: false },
            ]);
            
            await useTreeStore.getState().loadRootNodes();
            
            const { nodeCache } = useTreeStore.getState();
            expect(nodeCache.size).toBe(2);
            
            const ids = Array.from(nodeCache.keys());
            expect(ids[0]).not.toBe(ids[1]);
            expect(ids.some(id => id.includes('duplicate'))).toBe(true);
        });

        it('should generate unique IDs when duplicates are detected in children', async () => {
            useTreeStore.getState().reset();
            
            await useTreeStore.getState().loadRootNodes();
            
            const { api } = await import('@/services/api');
            vi.mocked(api.expandNode).mockResolvedValue({
                children: [
                    { id: 'dupChild', name: 'Child1', type: 'function' as const, childCount: 0, isExpanded: false },
                    { id: 'dupChild', name: 'Child2', type: 'function' as const, childCount: 0, isExpanded: false },
                ],
                outgoing: [],
            });
            
            await useTreeStore.getState().expandNode('pkg1');
            
            const { nodeCache } = useTreeStore.getState();
            const childIds = Array.from(nodeCache.keys()).filter(id => id.includes('dupChild'));
            
            expect(childIds.length).toBe(2);
            expect(childIds[0]).not.toBe(childIds[1]);
        });
    });

    describe('search race condition handling', () => {
        it('should prevent stale search results from overwriting newer ones', async () => {
            useTreeStore.getState().reset();
            
            const { api } = await import('@/services/api');
            
            let slowResolve: (value: unknown) => void;
            const slowPromise = new Promise(resolve => {
                slowResolve = resolve;
            });
            
            vi.mocked(api.search).mockImplementation(async (query: string) => {
                if (query === 'slow') {
                    return slowPromise;
                }
                return {
                    query,
                    results: [{ id: 'fast', name: 'Fast Result', type: 'class' as const, score: 1 }],
                    total: 1,
                };
            });
            
            const searchSlow = useTreeStore.getState().search('slow');
            
            await useTreeStore.getState().search('fast');
            
            slowResolve!({
                query: 'slow',
                results: [{ id: 'slow', name: 'Slow Result', type: 'class' as const, score: 1 }],
                total: 1,
            });
            
            await searchSlow;
            
            const { searchResults } = useTreeStore.getState();
            expect(searchResults.length).toBe(1);
            expect(searchResults[0].id).toBe('fast');
        });

        it('should cancel search results when navigating away', async () => {
            useTreeStore.getState().reset();
            
            const { api } = await import('@/services/api');
            
            let slowResolve: (value: unknown) => void;
            const slowPromise = new Promise(resolve => {
                slowResolve = resolve;
            });
            
            vi.mocked(api.search).mockImplementation(async () => slowPromise);
            vi.mocked(api.getNodeAncestors).mockResolvedValue([]);
            vi.mocked(api.expandNode).mockResolvedValue({ children: [], outgoing: [] });
            
            const searchPromise = useTreeStore.getState().search('test');
            
            await useTreeStore.getState().navigateToSearchResult('node1');
            
            slowResolve!({
                query: 'test',
                results: [{ id: 'stale', name: 'Stale', type: 'class' as const, score: 1 }],
                total: 1,
            });
            
            await searchPromise;
            
            const { searchResults, searchQuery } = useTreeStore.getState();
            expect(searchResults.length).toBe(0);
            expect(searchQuery).toBe('');
        });
    });

    describe('breadcrumb safety', () => {
        it('should handle circular parent references gracefully', async () => {
            useTreeStore.getState().reset();
            
            await useTreeStore.getState().loadRootNodes();
            
            const circularNodeId = 'circular_node';
            const store = useTreeStore.getState();
            
            const mockNodeCache = new Map(store.nodeCache);
            const circularNode = {
                id: circularNodeId,
                name: 'Circular',
                type: 'class' as const,
                childCount: 0,
                isExpanded: false,
                parentId: circularNodeId,
                depth: 1,
            };
            mockNodeCache.set(circularNodeId, circularNode);
            
            useTreeStore.setState({ nodeCache: mockNodeCache });
            
            store.selectNode(circularNodeId);
            
            const { breadcrumbPath } = useTreeStore.getState();
            expect(breadcrumbPath.length).toBe(1);
            expect(breadcrumbPath[0].id).toBe(circularNodeId);
        });

        it('should limit deeply nested breadcrumb paths', async () => {
            useTreeStore.getState().reset();
            
            await useTreeStore.getState().loadRootNodes();
            
            const store = useTreeStore.getState();
            
            const mockNodeCache = new Map(store.nodeCache);
            let parentId = 'pkg1';
            
            for (let i = 0; i < 1005; i++) {
                const nodeId = `node_${i}`;
                mockNodeCache.set(nodeId, {
                    id: nodeId,
                    name: `Node ${i}`,
                    type: 'function' as const,
                    childCount: 0,
                    isExpanded: false,
                    parentId,
                    depth: i,
                });
                parentId = nodeId;
            }
            
            useTreeStore.setState({ nodeCache: mockNodeCache });
            
            store.selectNode('node_1004');
            
            const { breadcrumbPath } = useTreeStore.getState();
            expect(breadcrumbPath.length).toBeLessThanOrEqual(1000);
        });

        it('should build correct breadcrumb path for normal nodes', async () => {
            useTreeStore.getState().reset();
            
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            useTreeStore.getState().selectNode('cls1');
            
            const { breadcrumbPath } = useTreeStore.getState();
            expect(breadcrumbPath.length).toBe(2);
            expect(breadcrumbPath[0].id).toBe('pkg1');
            expect(breadcrumbPath[1].id).toBe('cls1');
        });
    });

    describe('stale selectedNodeId handling', () => {
        it('should clear selectedNodeId when selected node is collapsed', async () => {
            useTreeStore.getState().reset();
            
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            useTreeStore.getState().selectNode('cls1');
            expect(useTreeStore.getState().selectedNodeId).toBe('cls1');
            
            useTreeStore.getState().collapseNode('pkg1');
            
            const { selectedNodeId } = useTreeStore.getState();
            expect(selectedNodeId).toBe(null);
        });

        it('should validate node exists before selecting', async () => {
            useTreeStore.getState().reset();
            
            await useTreeStore.getState().loadRootNodes();
            
            useTreeStore.getState().selectNode('nonexistent');
            
            const { selectedNodeId } = useTreeStore.getState();
            expect(selectedNodeId).toBe(null);
        });

        it('should not clear selectedNodeId when collapsing different branch', async () => {
            useTreeStore.getState().reset();
            
            await useTreeStore.getState().loadRootNodes();
            await useTreeStore.getState().expandNode('pkg1');
            
            useTreeStore.getState().selectNode('cls1');
            expect(useTreeStore.getState().selectedNodeId).toBe('cls1');
            
            useTreeStore.getState().collapseNode('mod1');
            
            expect(useTreeStore.getState().selectedNodeId).toBe('cls1');
        });
    });
});