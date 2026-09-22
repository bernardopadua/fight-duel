import { useState, type SubmitEvent } from "react";

//AUTH
import { login } from "@/api/auth";

//AUTH CONTEXT
import { useAuth } from "@/auth/auth-context";

//STORE
import { usePlayerStore } from "@/game/store/player-store";

//API
import { getPlayer } from "@/api/player";

export default function Login(
    { goGame, goRegister, goPlayerCreation } : 
    { goGame: () => void, goRegister: () => void, goPlayerCreation: () => void }
){
    const auth = useAuth();
    const [userName, setUserName] = useState<string>("test");
    const [password, setPassword] = useState<string>("testword");
    const [error, setError] = useState<string|null>(null);

    const setPlayer = usePlayerStore((s) => s.setPlayer);

    const handleSubmit = async (e: SubmitEvent) => {
        e.preventDefault();
        
        try {
            const response = await login(userName, password);
            if (!response) return;
            auth.login(response.token, response.oneTimeTicket);
            
            getPlayer(response.token)
            .then((player) => {
                if (!player) {
                    goPlayerCreation();
                } else {
                    setPlayer(player);
                    goGame();
                }
            });
        } catch (err){
            if(err instanceof Error){
                console.error(err.message);
            }
            setError("Usuário ou senha inválidos");
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input value={userName} onChange={(e) => setUserName(e.target.value)} placeholder="username" />
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="password" />
            {error ? <p>{error}</p> : <br />}
            <button type="submit">Login</button><br />
            <button type="button" onClick={goRegister}>Don't have an account?</button>
        </form>
    );
};