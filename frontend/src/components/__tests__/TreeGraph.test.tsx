/**
 * TreeGraph Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReactFlowProvider } from 'reactflow';
import { TreeGraph } from '../TreeGraph';
import { useTreeStore } from '@/stores/treeStore';

vi.mock('@/stores/treeStore', () => ({
    useTreeStore: vi.fn((selector) => {
        const state = {
            nodes: [],
            edges: [],
            isLoading: false,
            error: null,
            selectedNodeId: null,
            loadRootNodes: vi.fn(),
            onNodesChange: vi.fn(),
            onEdgesChange: vi.fn(),
            selectNode: vi.fn(),
            toggleNode: vi.fn(),
        };
        return selector(state);
    }),
    NODE_COLORS: {
        package: '#6366f1',
        module: '#8b5cf6',
        class: '#10b981',
        function: '#f59e0b',
        variable: '#ec4899',
        unknown: '#64748b',
    },
}));

vi.mock('@/stores/themeStore', () => ({
    useThemeStore: vi.fn((selector) =>
        selector({ mode: 'dark' })
    ),
}));

describe('TreeGraph', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('rendering states', () => {
        it('should show loading state when loading', () => {
            vi.mocked(useTreeStore).mockImplementation((selector) =>
                selector({
                    nodes: [],
                    edges: [],
                    isLoading: true,
                    error: null,
                    selectedNodeId: null,
                    loadRootNodes: vi.fn(),
                    onNodesChange: vi.fn(),
                    onEdgesChange: vi.fn(),
                    selectNode: vi.fn(),
                    toggleNode: vi.fn(),
                })
            );

            render(
                <ReactFlowProvider>
                    <TreeGraph />
                </ReactFlowProvider>
            );

            expect(screen.getByText('Loading code structure...')).toBeInTheDocument();
        });

        it('should show error state when there is an error', () => {
            vi.mocked(useTreeStore).mockImplementation((selector) =>
                selector({
                    nodes: [],
                    edges: [],
                    isLoading: false,
                    error: 'Failed to load graph',
                    selectedNodeId: null,
                    loadRootNodes: vi.fn(),
                    onNodesChange: vi.fn(),
                    onEdgesChange: vi.fn(),
                    selectNode: vi.fn(),
                    toggleNode: vi.fn(),
                })
            );

            render(
                <ReactFlowProvider>
                    <TreeGraph />
                </ReactFlowProvider>
            );

            expect(screen.getByText('Error: Failed to load graph')).toBeInTheDocument();
        });

        it('should show empty state when no nodes', () => {
            vi.mocked(useTreeStore).mockImplementation((selector) =>
                selector({
                    nodes: [],
                    edges: [],
                    isLoading: false,
                    error: null,
                    selectedNodeId: null,
                    loadRootNodes: vi.fn(),
                    onNodesChange: vi.fn(),
                    onEdgesChange: vi.fn(),
                    selectNode: vi.fn(),
                    toggleNode: vi.fn(),
                })
            );

            render(
                <ReactFlowProvider>
                    <TreeGraph />
                </ReactFlowProvider>
            );

            expect(screen.getByText('No Code Structure')).toBeInTheDocument();
        });
    });

    describe('fitView race condition prevention', () => {
        it('should cleanup pending fitView calls on unmount', () => {
            const clearTimeoutSpy = vi.spyOn(window, 'clearTimeout');

            const mockLoadRootNodes = vi.fn();
            
            vi.mocked(useTreeStore).mockImplementation((selector) => {
                const state = {
                    nodes: [{ id: 'node1', data: { label: 'Node 1' } }],
                    edges: [],
                    isLoading: false,
                    error: null,
                    selectedNodeId: null,
                    loadRootNodes: mockLoadRootNodes,
                    onNodesChange: vi.fn(),
                    onEdgesChange: vi.fn(),
                    selectNode: vi.fn(),
                    toggleNode: vi.fn(),
                };
                return selector(state);
            });

            const { unmount } = render(
                <ReactFlowProvider>
                    <TreeGraph />
                </ReactFlowProvider>
            );

            unmount();

            expect(clearTimeoutSpy).toHaveBeenCalled();
            
            clearTimeoutSpy.mockRestore();
        });
    });

    describe('setCenter race condition prevention', () => {
        it('should cleanup pending setCenter calls on unmount', () => {
            const clearTimeoutSpy = vi.spyOn(window, 'clearTimeout');

            const mockLoadRootNodes = vi.fn();
            const mockSelectNode = vi.fn();
            
            vi.mocked(useTreeStore).mockImplementation((selector) => {
                const state = {
                    nodes: [
                        { id: 'node1', data: { label: 'Node 1' }, position: { x: 0, y: 0 } },
                    ],
                    edges: [],
                    isLoading: false,
                    error: null,
                    selectedNodeId: 'node1',
                    loadRootNodes: mockLoadRootNodes,
                    onNodesChange: vi.fn(),
                    onEdgesChange: vi.fn(),
                    selectNode: mockSelectNode,
                    toggleNode: vi.fn(),
                };
                return selector(state);
            });

            const { unmount } = render(
                <ReactFlowProvider>
                    <TreeGraph />
                </ReactFlowProvider>
            );

            unmount();

            expect(clearTimeoutSpy).toHaveBeenCalled();
            
            clearTimeoutSpy.mockRestore();
        });
    });
});
