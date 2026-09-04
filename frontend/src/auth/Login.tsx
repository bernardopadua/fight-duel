import { useState, type SubmitEvent } from "react";
import { login } from "@/api/auth";
import { useAuth } from "./AuthContext";

export default function Login({ goRegister } : { goRegister: () => void }){
    const auth = useAuth();
    const [userName, setUserName] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [error, setError] = useState<string|null>(null);

    const handleSubmit = async (e: SubmitEvent) => {
        e.preventDefault();
        
        try {
            const response = await login(userName, password);
            if (!response) return;
            auth.login(response.token);
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