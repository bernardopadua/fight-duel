//REACT
import { useEffect, useState } from "react";

// CONTEXT
import { useAuth } from "../auth/AuthContext";

//TYPES
import type { Player } from "./types";

//API
import { getPlayer } from "../api/player";

//COMPONENTS
import PlayerCreation from "./PlayerCreation";
import GameLayout from "./GameLayout";

type PlayerStateView = 
    | { status: "loading" } 
    | { status: "no-player" } 
    | { status: "has-player", player: Player };

function Game(){
    const auth = useAuth();
    const [gameState, setGameState] = useState<PlayerStateView>({ status: "loading" });

    useEffect(() => {
        let ignore = false;
        if(!auth.token) return;

        getPlayer(auth.token)
            .then((player) => { 
                if (ignore) return;
                if (!player) {
                    setGameState({ status: "no-player" });
                    return;
                }

                setGameState({ status: "has-player", player: player });
            });

        return () => { ignore = true; }
    }, []);

    return (
        gameState.status === "loading" ? 
            <p>Loading...</p> : 
            gameState.status === "no-player" ?
                <PlayerCreation 
                    onPlayerCreation={(p: Player) => {setGameState({ status: "has-player", player: p });}}
                /> :
                <GameLayout player={gameState.player} />
    );
};

export default Game;