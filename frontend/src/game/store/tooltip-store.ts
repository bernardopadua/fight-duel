import { create } from 'zustand';
import type { Item } from '@/game/store/store-types';

export interface TooltipExtraInfo {
    isEquipped?: boolean;
    hint?: string;
}

interface TooltipState {
    visible: boolean;
    item: Item | null;
    coords: { x: number; y: number };
    extra?: TooltipExtraInfo;
    showTooltip: (item: Item, coords: { x: number; y: number }, extra?: TooltipExtraInfo) => void;
    updateCoords: (coords: { x: number; y: number }) => void;
    hideTooltip: () => void;
}

export const useTooltipStore = create<TooltipState>((set) => ({
    visible: false,
    item: null,
    coords: { x: 0, y: 0 },
    extra: undefined,
    showTooltip: (item, coords, extra) => set({ visible: true, item, coords, extra }),
    updateCoords: (coords) => set({ coords }),
    hideTooltip: () => set({ visible: false, item: null, extra: undefined }),
}));
