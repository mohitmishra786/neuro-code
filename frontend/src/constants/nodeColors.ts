/**
 * Single source of truth for graph node colors.
 * Keep in sync with CSS variables in App.css (--node-*).
 */

import type { NodeType } from '@/types/graph.types';

export const NODE_COLORS: Record<NodeType, string> = {
    package: '#6366f1', // Indigo — --node-package
    module: '#8b5cf6', // Purple — --node-module
    class: '#10b981', // Emerald — --node-class
    function: '#f59e0b', // Amber — --node-function
    variable: '#ec4899', // Pink — --node-variable
    unknown: '#64748b', // Slate
} as const;

export const EDGE_STYLES: Record<
    string,
    { label: string; color: string; strokeDasharray?: string; description: string }
> = {
    contains: {
        label: 'Contains',
        color: '#94a3b8',
        description: 'Hierarchy (package → module → class → function)',
    },
    calls: {
        label: 'Calls',
        color: '#f59e0b',
        strokeDasharray: '6 4',
        description: 'Function / method calls',
    },
    imports: {
        label: 'Imports',
        color: '#6366f1',
        strokeDasharray: '2 4',
        description: 'Import relationships',
    },
    inherits: {
        label: 'Inherits',
        color: '#10b981',
        description: 'Class inheritance',
    },
};

export const NODE_TYPE_LABELS: Record<NodeType, string> = {
    package: 'Package',
    module: 'Module',
    class: 'Class',
    function: 'Function',
    variable: 'Variable',
    unknown: 'Unknown',
};
