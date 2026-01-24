/**
 * NeuroCode UI Store
 *
 * Zustand store for UI state management.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UIState {
    // Sidebar
    sidebarOpen: boolean;
    sidebarWidth: number;

    // Theme
    theme: 'light' | 'dark';

    // View settings
    showLabels: boolean;
    showEdges: boolean;
    labelThreshold: number;

    // Layout
    layoutRunning: boolean;
    layoutSettings: {
        gravity: number;
        scalingRatio: number;
        slowDown: number;
    };

    // Filters
    typeFilters: Set<string>;
    complexityFilter: number | null;

    // Actions
    toggleSidebar: () => void;
    setSidebarWidth: (width: number) => void;
    toggleTheme: () => void;
    setTheme: (theme: 'light' | 'dark') => void;
    setShowLabels: (show: boolean) => void;
    setShowEdges: (show: boolean) => void;
    setLabelThreshold: (threshold: number) => void;
    setLayoutRunning: (running: boolean) => void;
    updateLayoutSettings: (settings: Partial<UIState['layoutSettings']>) => void;
    toggleTypeFilter: (type: string) => void;
    setComplexityFilter: (min: number | null) => void;
    resetFilters: () => void;
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
