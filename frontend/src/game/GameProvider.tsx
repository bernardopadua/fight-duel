import { useEffect, useState } from 'react';

//TYPES
import type { GameServices } from '@/game/game-context';

//CONTEXT
import { GameContext } from '@/game/game-context';

//SERVICES
import { createWebSocketService } from '@/game/services/ws-service';
import { createFightService } from '@/game/services/fight-service';
import { createPlayerService } from '@/game/services/player-service';

export function GameProvider({ children }: { children: React.ReactNode }) {
    const [services] = useState<GameServices>(() => ({
        websocketService: createWebSocketService(),
        fightService: createFightService(),
        playerService: createPlayerService()
    }));

    useEffect(() => {
        if (!services) return;

        services.websocketService.connect();
        return () => {
            services.websocketService.disconnect();
        }
    }, [services]);

    return (
        <GameContext.Provider value={services}>
            {children}
        </GameContext.Provider>
    );
}