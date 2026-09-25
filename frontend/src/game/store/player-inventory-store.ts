//ZUSTAND
import { create } from 'zustand';

//ITEM
import { type Item } from '@/game/store/store-types';

//PLAYER INVENTORY ITEM
export interface PlayerInventoryItem extends Item {}

//INTERFACE
interface PlayerInventoryStore {
    items: PlayerInventoryItem[];
    setInventoryItems: (items: PlayerInventoryItem[]) => void;
}

export const usePlayerInventoryStore = create<PlayerInventoryStore>((set) => ({
    items: [],
    setInventoryItems: (items: PlayerInventoryItem[]) => set({ items }),
}));