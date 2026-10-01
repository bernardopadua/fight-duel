// ZUSTAND
import { create } from 'zustand';

//TYPES
import type { Player, WorldInfo } from '@/game/types';

//INTERFACE
interface PlayerStoreState {
    player: Player | null;
    setPlayer: (player: Player) => void;
    setCurrency: (currency: number) => void;
    setTotalInventoryWeight: (weight: number) => void;
    setPlayerLife: (life: number) => void;
    setPlayerStamina: (stamina: number) => void;
    setPlayerLevel: (level: number) => void;
    setPlayerWorld: (world: WorldInfo) => void;
};

export const usePlayerStore = create<PlayerStoreState>()((set) => ({
    player: null,
    setPlayer: (player: Player) => set(() => ({ player })),
    setCurrency: (currency: number) => set((player) => (
        player.player ?
            { player: { ...player.player, playerCurrency: currency } }
            : { player: null }
    )),
    setTotalInventoryWeight: (weight: number) => set((player) => (
        player.player ?
            { player: { ...player.player, totalInventoryWeight: weight } }
            : { player: null }
    )),
    setPlayerLife: (life: number) => set((player) => (
        player.player ?
            { player: { ...player.player, playerLife: life } }
            : { player: null }
    )),
    setPlayerStamina: (stamina: number) => set((player) => (
        player.player ?
            { player: { ...player.player, playerStamina: stamina } }
            : { player: null }
    )),
    setPlayerLevel: (level: number) => set((player) => (
        player.player ?
            { player: { ...player.player, playerLevel: level } }
            : { player: null }
    )),
    setPlayerWorld: (world: WorldInfo) => {
        set((player) => player.player ? {
            player: {
                ...player.player,
                playerWorldInfo: world
            }
        } : { player: null });
    }
}));