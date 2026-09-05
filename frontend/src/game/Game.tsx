//REACT
import { useEffect, useState } from 'react';

//CONTEXT
import { useAuth } from '@/auth/auth-context';
import { useGameContext } from '@/game/game-context';

//COMPONENTS
import PlayerCreation from '@/game/PlayerCreation';
import GameLayout from '@/game/GameLayout';

type PlayerStateView = 
    | { status: "loading" } 
    | { status: "no-player" } 
    | { status: "has-player" }
    | { status: "no-worlds" };

function Game(){
    const auth = useAuth();
    const services = useGameContext();
    const [gameState, setGameState] = useState<PlayerStateView>({ status: "loading" });

    useEffect(() => {
        let ignore = false;
        if(!auth.token) return;

        if (auth.token && !ignore) {
            services.playerService.getPlayer(auth.token)
            .then((hasPlayer) => {
                if (hasPlayer) {
                    services.worldService.fetchWorlds(auth.token)
                    .then((gotWorlds) => { 
                        if(!gotWorlds) 
                            setGameState({ status: "no-worlds" }); 
                        else
                            setGameState({ status: "has-player" }); 
                    });
                } else {
                    setGameState({ status: "no-player" });
                }
            });
        }

        return () => { ignore = true; }
    }, [auth.token, services.playerService]);

    return (
        gameState.status === "loading" ? 
            <p>Loading...</p> 
        : gameState.status === "no-player" ?
            <PlayerCreation /> 
        : gameState.status === "has-player" ?
            <GameLayout />
        : 
            <p>No worlds available</p>
    );
};

export default Game;