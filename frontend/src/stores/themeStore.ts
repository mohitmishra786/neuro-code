/**
 * NeuroCode Theme Store
 *
 * Zustand store for theme management (dark/light mode).
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ThemeMode, THEMES } from '@/utils/colorScheme';

interface ThemeState {
    mode: ThemeMode;
    toggleTheme: () => void;
    setTheme: (mode: ThemeMode) => void;
}

export const useThemeStore = create<ThemeState>()(
    persist(
        (set, get) => ({
            mode: 'dark',

            toggleTheme: () => {
                const newMode = get().mode === 'dark' ? 'light' : 'dark';
                set({ mode: newMode });
                applyTheme(newMode);
            },

            setTheme: (mode: ThemeMode) => {
                set({ mode });
                applyTheme(mode);
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
    const theme = THEMES[mode];
    const root = document.documentElement;

    root.setAttribute('data-theme', mode);

    // Apply CSS custom properties
    root.style.setProperty('--color-background', theme.background);
    root.style.setProperty('--color-background-gradient', theme.backgroundGradient);
    root.style.setProperty('--color-surface', theme.surface);
    root.style.setProperty('--color-surface-glass', theme.surfaceGlass);
    root.style.setProperty('--color-surface-hover', theme.surfaceHover);
    root.style.setProperty('--color-surface-active', theme.surfaceActive);
    root.style.setProperty('--color-border', theme.border);
    root.style.setProperty('--color-border-hover', theme.borderHover);
    root.style.setProperty('--color-text', theme.text);
    root.style.setProperty('--color-text-secondary', theme.textSecondary);
    root.style.setProperty('--color-text-muted', theme.textMuted);
    root.style.setProperty('--color-accent', theme.accent);
    root.style.setProperty('--color-accent-hover', theme.accentHover);
    root.style.setProperty('--color-accent-glow', theme.accentGlow);
    root.style.setProperty('--color-success', theme.success);
    root.style.setProperty('--color-warning', theme.warning);
    root.style.setProperty('--color-error', theme.error);
    root.style.setProperty('--color-shadow', theme.shadow);
    root.style.setProperty('--color-canvas-background', theme.canvasBackground);
    root.style.setProperty('--color-edge', theme.edgeColor);
}

// Initialize theme on first load
if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('neurocode-theme');
    const mode: ThemeMode = stored ? JSON.parse(stored).state?.mode || 'dark' : 'dark';
    applyTheme(mode);
}

export default useThemeStore;
