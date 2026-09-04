//STORE
import { usePlayerStore } from '@/game/store/player-store';

//API
import { getPlayer } from "@/api/player";

export interface PlayerService {
    getPlayer: (token: string) => void;
};

export function createPlayerService(): PlayerService {
    const setPlayer = usePlayerStore((s) => s.setPlayer);

    return {
        getPlayer: async (token: string) => {
            getPlayer(token)
                .then((player) => { 
                    if (!player) {
                        return;
                    }
                    setPlayer(player);
                });
        }
    };
};
