import { useState, type SubmitEvent } from "react";
import { register } from "../api/auth";
import { useAuth } from "./AuthContext";

export default function Register({ goLogin } : { goLogin: () => void }){
    const auth = useAuth();
    const [userName, setUserName] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [error, setError] = useState<string|null>(null);

    const handleSubmit = async (e: SubmitEvent) => {
        e.preventDefault();
        
        try {
            const response = await register(userName, password);
            if ("error" in response){
                setError(response.error);
            } else {
                auth.login(response.token);
            }
        } catch (err){
            if(err instanceof Error){
                console.error(err.message);
            }
            setError("Erro ao registrar");
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input value={userName} onChange={(e) => setUserName(e.target.value)} placeholder="username" />
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="password" />
            {error && <p>{error}</p>}<br />
            <button type="submit">Create Account</button><br />
            <button type="button" onClick={goLogin}>I already have an account</button>
        </form>
    );
};