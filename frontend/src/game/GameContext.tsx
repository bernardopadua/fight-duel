import { createContext, useContext, useEffect } from 'react';

//SERVICES
import type { FightService } from '@/game/services/fight-service';
import type { WebSocketService } from '@/game/services/ws-service';
import type { PlayerService } from '@/game/services/player-service';
import { createWebSocketService } from '@/game/services/ws-service';
import { createFightService } from '@/game/services/fight-service';
import { createPlayerService } from '@/game/services/player-service';

type GameServicesType = {
    websocketService: WebSocketService;
    fightService: FightService;
    playerService: PlayerService;
};

const GameContext = createContext<GameServicesType | null>(null);

export function useGameContext() {
    const ctx = useContext(GameContext);
    if (!ctx) {
        throw new Error("useGameContext must be used within a GameProvider");
    }
    return ctx;
}

export function GameProvider({ children }: { children: React.ReactNode }) {
    const services: GameServicesType = {
        websocketService: createWebSocketService(),
        fightService: createFightService(),
        playerService: createPlayerService()
    };

    useEffect(() => {
        services.websocketService.connect();
        return () => {
            services.websocketService.disconnect();
        }
    }, []);

    return (
        <GameContext.Provider value={services}>
            {children}
        </GameContext.Provider>
    );
}