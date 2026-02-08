/**
 * NeuroCode UI Store
 *
 * Zustand store for UI state management.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

/** Layout settings configuration. */
interface LayoutSettings {
    /** Gravity factor for dagre layout. */
    readonly gravity: number;
    /** Scaling ratio for node spacing. */
    readonly scalingRatio: number;
    /** Slow down factor for animation. */
    readonly slowDown: number;
}

/** UI state interface with readonly properties. */
interface UIState {
    /** Whether the sidebar is open. */
    readonly sidebarOpen: boolean;
    /** Width of the sidebar in pixels. */
    readonly sidebarWidth: number;
    /** Current theme mode. */
    readonly theme: 'light' | 'dark';
    /** Whether to show node labels. */
    readonly showLabels: boolean;
    /** Whether to show edges. */
    readonly showEdges: boolean;
    /** Minimum child count to show labels. */
    readonly labelThreshold: number;
    /** Whether layout computation is running. */
    readonly layoutRunning: boolean;
    /** Layout algorithm settings. */
    readonly layoutSettings: Readonly<LayoutSettings>;
    /** Set of node types to filter. */
    readonly typeFilters: ReadonlySet<string>;
    /** Minimum complexity to show nodes, or null for no filter. */
    readonly complexityFilter: number | null;

    // Actions
    /** Toggle sidebar open/closed state. */
    readonly toggleSidebar: () => void;
    /** Set the sidebar width. */
    readonly setSidebarWidth: (width: number) => void;
    /** Toggle between light and dark theme. */
    readonly toggleTheme: () => void;
    /** Set the theme mode explicitly. */
    readonly setTheme: (theme: 'light' | 'dark') => void;
    /** Set whether to show labels. */
    readonly setShowLabels: (show: boolean) => void;
    /** Set whether to show edges. */
    readonly setShowEdges: (show: boolean) => void;
    /** Set the label display threshold. */
    readonly setLabelThreshold: (threshold: number) => void;
    /** Set whether layout is running. */
    readonly setLayoutRunning: (running: boolean) => void;
    /** Update layout settings. */
    readonly updateLayoutSettings: (settings: Partial<Readonly<LayoutSettings>>) => void;
    /** Toggle a type filter on/off. */
    readonly toggleTypeFilter: (type: string) => void;
    /** Set the minimum complexity filter. */
    readonly setComplexityFilter: (min: number | null) => void;
    /** Reset all filters to default. */
    readonly resetFilters: () => void;
}

export const useUIStore = create<UIState>()(
    devtools(
        persist(
            (set, _get) => ({
                // Initial state
                sidebarOpen: true,
                sidebarWidth: 320,
                theme: 'dark',
                showLabels: true,
                showEdges: true,
                labelThreshold: 6,
                layoutRunning: false,
                layoutSettings: {
                    gravity: 0.5,
                    scalingRatio: 2,
                    slowDown: 5,
                },
                typeFilters: new Set<string>(),
                complexityFilter: null,

                // Actions
                toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

                setSidebarWidth: (width) => set({ sidebarWidth: width }),

                toggleTheme: () =>
                    set((state) => ({
                        theme: state.theme === 'dark' ? 'light' : 'dark',
                    })),

                setTheme: (theme) => set({ theme }),

                setShowLabels: (show) => set({ showLabels: show }),

                setShowEdges: (show) => set({ showEdges: show }),

                setLabelThreshold: (threshold) => set({ labelThreshold: threshold }),

                setLayoutRunning: (running) => set({ layoutRunning: running }),

                updateLayoutSettings: (settings) =>
                    set((state) => ({
                        layoutSettings: { ...state.layoutSettings, ...settings },
                    })),

                toggleTypeFilter: (type) =>
                    set((state) => {
                        const newFilters = new Set(state.typeFilters);
                        if (newFilters.has(type)) {
                            newFilters.delete(type);
                        } else {
                            newFilters.add(type);
                        }
                        return { typeFilters: newFilters };
                    }),

                setComplexityFilter: (min) => set({ complexityFilter: min }),

                resetFilters: () =>
                    set({
                        typeFilters: new Set<string>(),
                        complexityFilter: null,
                    }),
            }),
            {
                name: 'neurocode-ui',
                partialize: (state) => ({
                    theme: state.theme,
                    sidebarWidth: state.sidebarWidth,
                    showLabels: state.showLabels,
                    showEdges: state.showEdges,
                    labelThreshold: state.labelThreshold,
                }),
            },
        ),
        { name: 'NeuroCodeUI' },
    ),
);

export default useUIStore;
