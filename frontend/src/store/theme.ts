import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ThemeMode } from '@/theme';

interface ThemeState {
  mode: ThemeMode;
  toggleMode: () => void;
  setMode: (mode: ThemeMode) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      mode: 'light',
      toggleMode: () =>
        set((state) => ({
          mode: state.mode === 'light' ? 'dark' : 'light',
        })),
      setMode: (mode) => set({ mode }),
    }),
    {
      name: 'vo-benchmark-theme',
      partialize: (state) => ({ mode: state.mode }),
    }
  )
);
