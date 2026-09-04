//REACT
import { useEffect, useState } from "react";

//CONTEXT
import { useAuth } from "@/auth/AuthContext";
import { useGameContext } from "./GameContext";

//COMPONENTS
import PlayerCreation from "./PlayerCreation";
import GameLayout from "./GameLayout";

type PlayerStateView = 
    | { status: "loading" } 
    | { status: "no-player" } 
    | { status: "has-player" };

function Game(){
    const auth = useAuth();
    const services = useGameContext();
    const [gameState, setGameState] = useState<PlayerStateView>({ status: "loading" });

    useEffect(() => {
        let ignore = false;
        if(!auth.token) return;

        if (auth.token && !ignore) {
            services.playerService.getPlayer(auth.token);
            setGameState({ status: "has-player" });
        }

        return () => { ignore = true; }
    }, []);

    return (
        gameState.status === "loading" ? 
            <p>Loading...</p> : 
            gameState.status === "no-player" ?
                <PlayerCreation /> :
                <GameLayout />
    );
};

export default Game;