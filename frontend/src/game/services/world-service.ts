//API
import { getWorlds } from '@/api/world';

//STORE
import { useWorldStore } from '@/game/store/world-store';
import { usePlayerStore } from '@/game/store/player-store';

// WEBSOCKET
import type { WebSocketService } from '@/game/services/ws-service';
import type { WebSocketRecoverStatusMessage } from '@/game/services/ws-messages';

//EVENT EMITTER
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

interface WorldService {
    fetchWorlds: (token: string) => Promise<boolean>;
};

function createWorldService(ws: WebSocketService): WorldService {
    
    const respRecoverStatus = (message: WebSocketRecoverStatusMessage) => {
        const { data } = message;
        usePlayerStore.getState().setPlayerLife(data.playerLife);
        usePlayerStore.getState().setPlayerStamina(data.playerStamina);
        EventBus.emit(GAME_EVENTS.PLAYER_RECOVER_STATUS);
    };
    ws.subscribe("player.recover.status", respRecoverStatus);
    
    return {
        fetchWorlds: async (token: string) => {
            const worlds = await getWorlds(token);
            if (worlds) {
                useWorldStore.getState().setWorlds(worlds);
                return true;
            }
            return false;
        }
    };
};

export { createWorldService, type WorldService };
