import { create } from 'zustand';

//TYPES
import type { WorldInfo } from '@/game/types';

//INTERFACE
interface WorldStoreState {
    worlds: WorldInfo[];
    setWorlds: (worlds: WorldInfo[]) => void;
    getWorldId: (id: number) => WorldInfo | null;
};

export const useWorldStore = create<WorldStoreState>()((set, get) => ({
    worlds: [],
    setWorlds: (worlds: WorldInfo[]) => set(() => ({ worlds })),
    getWorldId: (id: number) => {
        return get().worlds.find((world) => {
            if(world.id === id) return world;
        }) ?? null;
    }
}));