import { ApiError, callFetch } from "./api";

import { ROUTES } from "./routes";
import type { Player } from "@/game/types";

import type { PlayerCreationPayload } from "./types";

export async function getPlayer(token: string): Promise<Player | null> {
    try{
        return await callFetch<Player>(ROUTES.getPlayer(), token);
    } catch (err){
        if (err instanceof ApiError) {
            console.log(err.error);
        }
        return null;
    }
};

export async function createPlayer(token: string, player: PlayerCreationPayload): Promise<Player | null> {
    try{
        return await callFetch<Player>(ROUTES.createPlayer(), token, {method: "POST", body: JSON.stringify(player)});
    } catch (err) {
        if (err instanceof ApiError) {
            console.log(err.error);
        }
        return null;
    }
};