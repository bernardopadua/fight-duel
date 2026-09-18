import { useEffect, useState } from 'react';

//CONTEXT
import { useAuth } from '@/auth/auth-context';
import { useGameContext } from '@/game/game-context';

//COMPONENTS
import GameLayout from '@/game/GameLayout';
import { usePlayerStore } from './store/player-store';

type PlayerStateView =
    | { status: "loading" }
    | { status: "has-player" }
    | { status: "no-worlds" };

export default function GameLoggedIn() {
    const auth = useAuth();
    const services = useGameContext();
    const player = usePlayerStore((s) => s.player);
    const [gameState, setGameState] = useState<PlayerStateView>({ status: "loading" });

    useEffect(() => {
        let ignore = false;
        if (!auth.token) return;

        if (!player){
            auth.logout();
            return;
        }

        if (auth.token && !ignore) {
            services.worldService.fetchWorlds(auth.token)
                .then((gotWorlds) => {
                    if (ignore) return;
                    if (!gotWorlds)
                        setGameState({ status: "no-worlds" });
                    else
                        setGameState({ status: "has-player" });
                });
        }
        return () => { ignore = true; }
    }, [services.worldService]);

    return (
        gameState.status === "loading" ?
            <p>Loading...</p>
            : gameState.status === "has-player" ?
                <GameLayout />
                :
                <p>No worlds available</p>
    );
}