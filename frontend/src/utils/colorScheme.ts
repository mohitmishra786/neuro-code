/**
 * NeuroCode Color Scheme
 *
 * Premium, dynamic colors with dark/light mode support.
 */

import { NodeType, RelationshipType } from '@/types/graph.types';

// Premium gradient colors for nodes
export const NODE_COLORS: Record<NodeType, { base: string; light: string; glow: string }> = {
    module: {
        base: '#6366f1',     // Indigo
        light: '#818cf8',
        glow: 'rgba(99, 102, 241, 0.4)',
    },
    class: {
        base: '#10b981',     // Emerald
        light: '#34d399',
        glow: 'rgba(16, 185, 129, 0.4)',
    },
    function: {
        base: '#f59e0b',     // Amber
        light: '#fbbf24',
        glow: 'rgba(245, 158, 11, 0.4)',
    },
    variable: {
        base: '#ec4899',     // Pink
        light: '#f472b6',
        glow: 'rgba(236, 72, 153, 0.4)',
    },
    unknown: {
        base: '#6b7280',     // Gray
        light: '#9ca3af',
        glow: 'rgba(107, 114, 128, 0.4)',
    },
};

export const EDGE_COLORS: Record<RelationshipType, string> = {
    CONTAINS: 'rgba(148, 163, 184, 0.5)',  // Slate with transparency
    CALLS: '#ef4444',                       // Red
    IMPORTS: '#6366f1',                     // Indigo
    INHERITS: '#10b981',                    // Emerald
    INSTANTIATES: '#f59e0b',                // Amber
    DECORATES: '#a855f7',                   // Purple
    DEFINES: '#14b8a6',                     // Teal
    USES: '#84cc16',                        // Lime
};

// Theme-aware colors
export const THEMES = {
    dark: {
        background: '#0a0a0f',
        backgroundGradient: 'radial-gradient(ellipse at 50% 0%, rgba(99, 102, 241, 0.08) 0%, transparent 50%)',
        surface: '#111118',
        surfaceGlass: 'rgba(17, 17, 24, 0.8)',
        surfaceHover: '#1a1a24',
        surfaceActive: '#222230',
        border: 'rgba(148, 163, 184, 0.1)',
        borderHover: 'rgba(148, 163, 184, 0.2)',
        text: '#f8fafc',
        textSecondary: '#94a3b8',
        textMuted: '#475569',
        accent: '#6366f1',
        accentHover: '#818cf8',
        accentGlow: 'rgba(99, 102, 241, 0.3)',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        shadow: 'rgba(0, 0, 0, 0.5)',
        canvasBackground: '#050508',
        edgeColor: 'rgba(148, 163, 184, 0.3)',
    },
    light: {
        background: '#f8fafc',
        backgroundGradient: 'radial-gradient(ellipse at 50% 0%, rgba(99, 102, 241, 0.05) 0%, transparent 50%)',
        surface: '#ffffff',
        surfaceGlass: 'rgba(255, 255, 255, 0.9)',
        surfaceHover: '#f1f5f9',
        surfaceActive: '#e2e8f0',
        border: 'rgba(148, 163, 184, 0.2)',
        borderHover: 'rgba(148, 163, 184, 0.4)',
        text: '#0f172a',
        textSecondary: '#475569',
        textMuted: '#94a3b8',
        accent: '#6366f1',
        accentHover: '#4f46e5',
        accentGlow: 'rgba(99, 102, 241, 0.2)',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        shadow: 'rgba(0, 0, 0, 0.1)',
        canvasBackground: '#fafbfc',
        edgeColor: 'rgba(100, 116, 139, 0.4)',
    },
};

export type ThemeMode = 'dark' | 'light';

export const UI_COLORS = THEMES.dark; // Default, but should be dynamically set

export function getNodeColor(type: NodeType, isExpanded: boolean = false): string {
    const colors = NODE_COLORS[type] || NODE_COLORS.unknown;
    return isExpanded ? colors.light : colors.base;
}

export function getNodeGlow(type: NodeType): string {
    const colors = NODE_COLORS[type] || NODE_COLORS.unknown;
    return colors.glow;
}

export function getEdgeColor(type: RelationshipType): string {
    return EDGE_COLORS[type] || EDGE_COLORS.CONTAINS;
}

// Helper for consistent sizing
export function getNodeSize(childCount: number, isExpanded: boolean): number {
    const base = 12;
    const childBonus = Math.min(childCount * 0.5, 8);
    const expandedBonus = isExpanded ? 4 : 0;
    return base + childBonus + expandedBonus;
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
