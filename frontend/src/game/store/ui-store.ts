//ZUSTAND
import { create } from 'zustand';

export type WindowId = 'inventory' | 'playerStats';

interface UIStore {
    windows: Record<WindowId, boolean>;
    open: (id: WindowId) => void;
    close: (id: WindowId) => void;
    toggle: (id: WindowId) => void;
}

export const useUIStore = create<UIStore>((set) => ({
    windows: {
        inventory: false,
        playerStats: false,
    },
    open: (id) => set((s) => ({ windows: { ...s.windows, [id]: true } })),
    close: (id) => set((s) => ({ windows: { ...s.windows, [id]: false } })),
    toggle: (id) => set((s) => ({ windows: { ...s.windows, [id]: !s.windows[id] } })),
}));
