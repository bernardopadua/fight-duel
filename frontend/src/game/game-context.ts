import { createContext, useContext } from "react";

//TYPES
import type { FightService } from "@/game/services/fight-service";
import type { WebSocketService } from "@/game/services/ws-service";
import type { PlayerService } from "@/game/services/player-service";

export interface GameServices {
    websocketService: WebSocketService;
    fightService: FightService;
    playerService: PlayerService;
};

export const GameContext = createContext<GameServices | null>(null);

export function useGameContext() {
    const ctx = useContext(GameContext);
    if (!ctx) {
        throw new Error("useGameContext must be used within a GameProvider");
    }
    return ctx;
}