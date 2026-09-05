import { ApiError, callFetch } from "./api";

import { ROUTES } from "./routes";
import type { WorldInfo } from "@/game/types";

export async function getWorlds(token: string): Promise<WorldInfo[] | null> {
    try{
        return await callFetch<WorldInfo[]>(ROUTES.getWorlds(), token);
    } catch (err){
        if (err instanceof ApiError) {
            console.log(err.error);
        }
        return null;
    }
};