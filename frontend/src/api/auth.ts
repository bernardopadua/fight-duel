import { ApiError, callFetch } from "./api";
import type { LoginResponse, RegisterResponse } from "./types";
import { ROUTES } from "./routes";

export async function login(username: string, password: string): Promise<LoginResponse | null>{
    try {
        const response = await callFetch<LoginResponse>(ROUTES.login(), null, {
            method: "POST",
            body: JSON.stringify({
                username,
                password
            })
        });

        return response;
    } catch (err) {
        console.log(err);
        return null;
    }
}

export async function register(username: string, password: string): Promise<RegisterResponse>{
    try {
        const response = await callFetch<RegisterResponse>(ROUTES.register(), null, {
            method: "POST",
            body: JSON.stringify({
                username,
                password
            })
        });

        return response;
    } catch (err) {
        console.log(err);
        if (err instanceof ApiError) return { error: err.error };
        return { error: "unknown error" };
    }
}