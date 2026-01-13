/**
 * useGraphData Hook
 *
 * Manages graph data fetching and caching.
 */

import { useCallback, useEffect } from 'react';
import { useGraphStore } from '@/stores/graphStore';
import { api } from '@/services/api';
import { GraphNode } from '@/types/graph.types';

interface UseGraphDataOptions {
    autoLoad?: boolean;
}

export function useGraphData(options: UseGraphDataOptions = {}) {
    const { autoLoad = true } = options;

    const nodes = useGraphStore((s) => s.nodes);
    const isLoading = useGraphStore((s) => s.isLoading);
    const error = useGraphStore((s) => s.error);
    const loadRootNodes = useGraphStore((s) => s.loadRootNodes);
    const expandNode = useGraphStore((s) => s.expandNode);

    // Auto-load root nodes on mount
    useEffect(() => {
        if (autoLoad && nodes.size === 0) {
            loadRootNodes();
        }
    }, [autoLoad, nodes.size, loadRootNodes]);

    const getNode = useCallback(
        async (nodeId: string): Promise<GraphNode | null> => {
            // Check cache first
            const cached = nodes.get(nodeId);
            if (cached) return cached;

            // Fetch from API
            try {
                return await api.getNode(nodeId);
            } catch {
                return null;
            }
        },
        [nodes],
    );

    const getChildren = useCallback(
        async (nodeId: string): Promise<GraphNode[]> => {
            try {
                return await api.getNodeChildren(nodeId);
            } catch {
                return [];
            }
        },
        [],
    );

    const prefetch = useCallback(
        async (nodeIds: string[]) => {
            // Prefetch nodes that aren't cached
            const uncached = nodeIds.filter((id) => !nodes.has(id));
            await Promise.all(uncached.map((id) => expandNode(id)));
        },
        [nodes, expandNode],
    );

    return {
        nodes,
        isLoading,
        error,
        loadRootNodes,
        expandNode,
        getNode,
        getChildren,
        prefetch,
    };
}

export default useGraphData;
