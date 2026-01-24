/**
 * NeuroCode Theme Store
 *
 * Zustand store for theme management (dark/light mode).
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
    mode: ThemeMode;
    toggleTheme: () => void;
    setTheme: (mode: ThemeMode) => void;
}

export const useThemeStore = create<ThemeState>()(
    persist(
        (set) => ({
            mode: 'dark',

            toggleTheme: () => {
                set((state) => {
                    const newMode = state.mode === 'dark' ? 'light' : 'dark';
                    applyTheme(newMode);
                    return { mode: newMode };
                });
            },

            setTheme: (mode: ThemeMode) => {
                applyTheme(mode);
                set({ mode });
            },
        }),
        {
            name: 'neurocode-theme',
            onRehydrateStorage: () => (state) => {
                if (state) {
                    applyTheme(state.mode);
                }
            },
        }
    )
);

function applyTheme(mode: ThemeMode) {
    if (typeof document === 'undefined') return;
    document.documentElement.setAttribute('data-theme', mode);
}

// Initialize theme on first load
if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('neurocode-theme');
    try {
        const mode: ThemeMode = stored ? JSON.parse(stored).state?.mode || 'dark' : 'dark';
        applyTheme(mode);
    } catch {
        applyTheme('dark');
    }
}

export default useThemeStore;
