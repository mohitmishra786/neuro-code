/**
 * NeuroCode Theme Store
 *
 * Zustand store for theme management (dark/light mode).
 * Uses blocking initialization to prevent FOUC.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
    mode: ThemeMode;
    toggleTheme: () => void;
    setTheme: (mode: ThemeMode) => void;
}

const getInitialTheme = (): ThemeMode => {
    if (typeof window === 'undefined') return 'dark';

    const stored = localStorage.getItem('neurocode-theme');
    if (stored) {
        try {
            const parsed = JSON.parse(stored);
            return (parsed.state?.mode as ThemeMode) || 'dark';
        } catch {
            return 'dark';
        }
    }
    return 'dark';
};

function applyTheme(mode: ThemeMode): void {
    if (typeof document === 'undefined') return;
    document.documentElement.setAttribute('data-theme', mode);
}

export const useThemeStore = create<ThemeState>()(
    persist(
        (set, get) => ({
            mode: getInitialTheme(),

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

if (typeof window !== 'undefined') {
    applyTheme(useThemeStore.getState().mode);
}

export default useThemeStore;
