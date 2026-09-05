//STORE
import { usePlayerStore } from '@/game/store/player-store';

//API
import { getPlayer } from "@/api/player";

export interface PlayerService {
    getPlayer: (token: string) => Promise<boolean>;
};

export function createPlayerService(): PlayerService {

    return {
        getPlayer: async (token: string) => {
            const player = await getPlayer(token);
            if (player) {
                usePlayerStore.getState().setPlayer(player);
                return true;
            } else {
                return false;
            }
        }
    };
};
