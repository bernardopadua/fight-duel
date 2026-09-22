import { useState } from "react";

//CONTEXTS
import { useAuth } from "@/auth/auth-context";
import { GameProvider } from "@/game/GameProvider";

//VIEWS
import Login from "@/auth/Login";
import Register from "@/auth/Register";
import Game from "@/game/Game";
import PlayerCreation from "@/game/PlayerCreation";

type View = "login" | "register" | "player-creation" | "game";

function App() {
    const auth = useAuth();
    const [view, setView] = useState<View>("login");
    
    if (!auth.token) {
        return (
            view === "login" ?
                <Login 
                    goGame={() => setView("game")} 
                    goRegister={() => setView("register")} 
                    goPlayerCreation={() => setView("player-creation")}
                />
            :
                <Register goPlayerCreation={() => setView("player-creation")} />
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