//ZUSTAND
import { create } from 'zustand';

//ITEM
import { type Item } from '@/game/store/store-types';

//DROPITEM
export interface DropItem extends Item {}

//INTERFACE
interface DropStore {
    items: DropItem[];
    setItems: (items: DropItem[]) => void;
}

export const useDropStore = create<DropStore>((set) => ({
    items: [],
    setItems: (items: DropItem[]) => set({ items }),
}));