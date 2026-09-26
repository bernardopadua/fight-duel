//ZUSTAND
import { create } from 'zustand';

export type WindowId = 
    | 'inventory' 
    | 'playerStats'
    | 'dropItems';

interface UIWindow {
    open: boolean,
    initialPosition?: {x: number, y: number}
}

interface UIStore {
    windows: Record<WindowId, UIWindow>;
    open: (id: WindowId) => void;
    close: (id: WindowId) => void;
    toggle: (id: WindowId) => void;
    setInitialPosition: (id: WindowId, position: {x: number, y: number}) => void;
}

export const useUIStore = create<UIStore>((set) => ({
    windows: {
        inventory: {open: false},
        playerStats: {open: false},
        dropItems: {open: false},
    },
    open: (id) => set((s) => ({ windows: { ...s.windows, [id]: { ...s.windows[id], open: true} } })),
    close: (id) => set((s) => ({ windows: { ...s.windows, [id]: { ...s.windows[id], open: false} } })),
    toggle: (id) => set((s) => ({ windows: { ...s.windows, [id]: { ...s.windows[id], open: !s.windows[id].open} } })),
    setInitialPosition: (id, position) => set((s) => ({ windows: { ...s.windows, [id]: { ...s.windows[id], initialPosition: position} } })),
}));
