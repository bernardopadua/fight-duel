import { create } from 'zustand';

//TYPES
import type { Player } from '@/game/types';

//INTERFACE
interface PlayerStoreState {
    player: Player | null;
    setPlayer: (player: Player) => void;
};

export const usePlayerStore = create<PlayerStoreState>()((set) => ({
    player: null,
    setPlayer: (player: Player) => set(() => ({ player }))
}));