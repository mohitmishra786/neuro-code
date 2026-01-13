/**
 * useGraphNavigation Hook
 *
 * Handles graph navigation, zoom, and focus.
 */

import { useCallback, useRef } from 'react';
import { useSigma } from '@react-sigma/core';
import { useGraphStore } from '@/stores/graphStore';

export function useGraphNavigation() {
    const sigma = useSigma();
    const selectNode = useGraphStore((s) => s.selectNode);
    const expandNode = useGraphStore((s) => s.expandNode);
    const focusNode = useGraphStore((s) => s.focusNode);
    const selectedNodeId = useGraphStore((s) => s.selectedNodeId);

    const animationRef = useRef<number | null>(null);

    const centerOnNode = useCallback(
        (nodeId: string, animate = true) => {
            const graph = sigma.getGraph();
            if (!graph.hasNode(nodeId)) return;

            const { x, y } = graph.getNodeAttributes(nodeId);
            const camera = sigma.getCamera();

            if (animate) {
                camera.animate({ x, y, ratio: 0.5 }, { duration: 300 });
            } else {
                camera.setState({ x, y, ratio: camera.ratio });
            }
        },
        [sigma],
    );

    const zoomIn = useCallback(
        (factor = 1.5) => {
            const camera = sigma.getCamera();
            camera.animate({ ratio: camera.ratio / factor }, { duration: 200 });
        },
        [sigma],
    );

    const zoomOut = useCallback(
        (factor = 1.5) => {
            const camera = sigma.getCamera();
            camera.animate({ ratio: camera.ratio * factor }, { duration: 200 });
        },
        [sigma],
    );

    const resetView = useCallback(() => {
        const camera = sigma.getCamera();
        camera.animate({ x: 0.5, y: 0.5, ratio: 1 }, { duration: 300 });
    }, [sigma]);

    const fitToContent = useCallback(() => {
        const graph = sigma.getGraph();
        const nodes = graph.nodes();

        if (nodes.length === 0) return;

        let minX = Infinity,
            maxX = -Infinity,
            minY = Infinity,
            maxY = -Infinity;

        nodes.forEach((nodeId) => {
            const { x, y } = graph.getNodeAttributes(nodeId);
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x);
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
        });

        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        const width = maxX - minX;
        const height = maxY - minY;
        const ratio = Math.max(width, height) / 500 + 0.5;

        sigma.getCamera().animate({ x: centerX, y: centerY, ratio }, { duration: 300 });
    }, [sigma]);

    const navigateToNode = useCallback(
        async (nodeId: string) => {
            await focusNode(nodeId);
            centerOnNode(nodeId);
        },
        [focusNode, centerOnNode],
    );

    const navigateToParent = useCallback(async () => {
        if (!selectedNodeId) return;

        const ancestors = await import('@/services/api').then((m) =>
            m.api.getNodeAncestors(selectedNodeId),
        );

        if (ancestors.length > 0) {
            const parent = ancestors[ancestors.length - 1];
            selectNode(parent.id);
            centerOnNode(parent.id);
        }
    }, [selectedNodeId, selectNode, centerOnNode]);

    return {
        centerOnNode,
        zoomIn,
        zoomOut,
        resetView,
        fitToContent,
        navigateToNode,
        navigateToParent,
    };
}

export default useGraphNavigation;
