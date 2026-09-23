import { useEffect, useState } from 'react';

// TYPES
import type { GameServices } from '@/game/game-context';

// CONTEXT
import { GameContext } from '@/game/game-context';
import { useAuth } from '@/auth/auth-context';

// SERVICES
import { createWebSocketService } from '@/game/services/ws-service';
import { createFightService } from '@/game/services/fight-service';
import { createPlayerService } from '@/game/services/player-service';
import { createWorldService } from '@/game/services/world-service';

export function GameProvider({ children }: { children: React.ReactNode }) {
    const auth = useAuth();
    const [services] = useState<GameServices>(() => {
        const ws = createWebSocketService();
        return {
            websocketService: ws,
            fightService: createFightService(ws),
            playerService: createPlayerService(ws),
            worldService: createWorldService(ws)
        };
    });

    useEffect(() => {
        if (!services) return;
        services.websocketService.connect(auth.ticket);
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