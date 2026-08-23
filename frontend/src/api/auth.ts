import type { LoginResponse, RegisterResponse } from "./types";
import { ROUTES } from "./routes";

export async function login(username: string, password: string): Promise<LoginResponse>{
    const response = await fetch(ROUTES.login(),{
        method: "POST",
        body: JSON.stringify({
            username,
            password
        }),
        headers: {
            "Content-Type": "application/json",
        },
    });

    if(!response.ok) throw new Error(`login failed: ${response.body}`);

    return response.json();
}

export async function register(username: string, password: string): Promise<RegisterResponse>{
    const response = await fetch(ROUTES.register(),{
        method: "POST",
        body: JSON.stringify({
            username,
            password
        }),
        headers: {
            "Content-Type": "application/json",
        },
    });

    if(!response.ok) throw new Error(`register failed: ${response.body}`);

    return response.json();
}