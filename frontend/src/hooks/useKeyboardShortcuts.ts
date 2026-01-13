/**
 * useKeyboardShortcuts Hook
 *
 * Handles keyboard shortcuts for the application.
 */

import { useEffect, useCallback } from 'react';
import { useGraphStore } from '@/stores/graphStore';

interface ShortcutConfig {
    key: string;
    ctrlKey?: boolean;
    metaKey?: boolean;
    shiftKey?: boolean;
    action: () => void;
    description: string;
}

export function useKeyboardShortcuts() {
    const selectNode = useGraphStore((s) => s.selectNode);
    const collapseNode = useGraphStore((s) => s.collapseNode);
    const refresh = useGraphStore((s) => s.refresh);
    const selectedNodeId = useGraphStore((s) => s.selectedNodeId);

    const shortcuts: ShortcutConfig[] = [
        {
            key: 'Escape',
            action: () => selectNode(null),
            description: 'Deselect current node',
        },
        {
            key: 'r',
            ctrlKey: true,
            action: () => refresh(),
            description: 'Refresh graph',
        },
        {
            key: 'r',
            metaKey: true,
            action: () => refresh(),
            description: 'Refresh graph (Mac)',
        },
        {
            key: 'c',
            action: () => {
                if (selectedNodeId) {
                    collapseNode(selectedNodeId);
                }
            },
            description: 'Collapse selected node',
        },
    ];

    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            // Ignore if typing in an input
            if (
                event.target instanceof HTMLInputElement ||
                event.target instanceof HTMLTextAreaElement
            ) {
                return;
            }

            for (const shortcut of shortcuts) {
                const matchesKey = event.key === shortcut.key || event.key.toLowerCase() === shortcut.key.toLowerCase();
                const matchesCtrl = !shortcut.ctrlKey || event.ctrlKey;
                const matchesMeta = !shortcut.metaKey || event.metaKey;
                const matchesShift = !shortcut.shiftKey || event.shiftKey;

                if (matchesKey && matchesCtrl && matchesMeta && matchesShift) {
                    event.preventDefault();
                    shortcut.action();
                    return;
                }
            }
        },
        [shortcuts],
    );

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);

    return {
        shortcuts: shortcuts.map((s) => ({
            key: s.key,
            modifiers: [
                s.ctrlKey && 'Ctrl',
                s.metaKey && 'Cmd',
                s.shiftKey && 'Shift',
            ].filter(Boolean),
            description: s.description,
        })),
    };
}

export default useKeyboardShortcuts;
