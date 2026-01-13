/**
 * NeuroCode Color Scheme
 *
 * Consistent colors for node and edge types.
 */

import { NodeType, RelationshipType } from '@/types/graph.types';

export const NODE_COLORS: Record<NodeType, string> = {
    module: '#4A90E2',    // Blue
    class: '#7ED321',     // Green
    function: '#F5A623',  // Orange
    variable: '#BD10E0',  // Purple
    unknown: '#9B9B9B',   // Gray
};

export const EDGE_COLORS: Record<RelationshipType, string> = {
    CONTAINS: '#E0E0E0',     // Light Gray
    CALLS: '#D0021B',        // Red
    IMPORTS: '#4A90E2',      // Blue
    INHERITS: '#7ED321',     // Green
    INSTANTIATES: '#F5A623', // Orange
    DECORATES: '#9013FE',    // Purple
    DEFINES: '#50E3C2',      // Teal
    USES: '#B8E986',         // Light Green
};

export const UI_COLORS = {
    background: '#1a1a2e',
    surface: '#16213e',
    surfaceHover: '#1f3460',
    border: '#2a3f5f',
    text: '#e8e8e8',
    textSecondary: '#a0a0a0',
    textMuted: '#6b6b6b',
    accent: '#4A90E2',
    accentHover: '#5da0f2',
    success: '#7ED321',
    warning: '#F5A623',
    error: '#D0021B',
};

export function getNodeColor(type: NodeType, isExpanded: boolean = false): string {
    const baseColor = NODE_COLORS[type] || NODE_COLORS.unknown;
    if (!isExpanded) {
        return baseColor;
    }
    // Slightly lighter when expanded
    return lightenColor(baseColor, 0.1);
}

export function getEdgeColor(type: RelationshipType): string {
    return EDGE_COLORS[type] || EDGE_COLORS.CONTAINS;
}

function lightenColor(hex: string, amount: number): string {
    const num = parseInt(hex.replace('#', ''), 16);
    const r = Math.min(255, Math.floor((num >> 16) + amount * 255));
    const g = Math.min(255, Math.floor(((num >> 8) & 0x00FF) + amount * 255));
    const b = Math.min(255, Math.floor((num & 0x0000FF) + amount * 255));
    return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`;
}

export function hexToRgba(hex: string, alpha: number): string {
    const num = parseInt(hex.replace('#', ''), 16);
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
