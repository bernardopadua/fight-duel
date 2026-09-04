import { useState } from "react";

//CONTEXTS
import { useAuth } from "./auth/AuthContext";
import { GameProvider } from "./game/GameContext";

//VIEWS
import Login from "./auth/Login";
import Register from "./auth/Register";
import Game from "./game/Game";

type View = "login" | "register" | "game";

function App() {
    const auth = useAuth();
    const [view, setView] = useState<View>("login");
    
    if(!auth.token){
        return (
            view === "login" ?
                <Login goRegister={() => setView("register")} /> :
                <Register goLogin={() => setView("login")} />
        );
    }

    return (
        <GameProvider>
            <Game />
        </GameProvider>
    );
}

export default App;