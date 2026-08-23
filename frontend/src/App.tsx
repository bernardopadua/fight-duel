import { useState } from "react";

import { useAuth } from "./auth/AuthContext";

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
        <Game />
    )
}

export default App;