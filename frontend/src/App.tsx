import { useState, useEffect } from "react";

//CONTEXTS
import { useAuth } from "@/auth/auth-context";
import { GameProvider } from "@/game/GameProvider";

//API
import { getPlayer } from "@/api/player";

//VIEWS
import Login from "@/auth/Login";
import Register from "@/auth/Register";
import Game from "@/game/Game";
import PlayerCreation from "@/game/PlayerCreation";
import { usePlayerStore } from "./game/store/player-store";

type View = "login" | "register" | "player-creation" | "game";

function App() {
    const auth = useAuth();
    const setPlayer = usePlayerStore((s) => s.setPlayer);
    const [view, setView] = useState<View>("login");

    useEffect(() => {
        if(!auth.token) return;

        //Player is registered ?
        getPlayer(auth.token!)
            .then((player) => {
                if (!player) {
                    setView("player-creation");
                } else {
                    setPlayer(player);
                    setView("game");
                }
            });
    }, []);

    if (!auth.token) {
        return (
            view === "login" ?
                <Login goRegister={() => setView("register")} />
            :
                <Register goLogin={() => setView("login")} />
        );
    }

    if (view === "player-creation"){
        return (
            <PlayerCreation goGame={() => setView("game")} />
        );
    } else if(view === "game") {
        return (
            <GameProvider>
                <Game />      
            </GameProvider>
        );
    }

    return (<h2>Loading...</h2>)
}

export default App;