// STORE
import { usePlayerStore } from '@/game/store/player-store';

// WEBSOCKET
import type { WebSocketService } from "@/game/services/ws-service";

// WSocket MESSAGE
import type { 
    WebSocketWorldEnterMessage,
    WebSocketSendEnterWorldMessage
 } from '@/game/services/ws-messages';

// EVENT EMITTER
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

//API
import { getPlayer } from "@/api/player";

export interface PlayerService {
    getPlayer: (token: string) => Promise<boolean>;
    enterWorld: (worldId: number) => void;
    leaveWorld: () => void;
};

export function createPlayerService(ws: WebSocketService): PlayerService {

    const respEnterWorld = (message: WebSocketWorldEnterMessage) => {
        usePlayerStore.getState().setPlayerWorld(message.data);
        EventBus.emit(GAME_EVENTS.ENTER_WORLD, message.data);
    };

    ws.subscribe('world.enter', respEnterWorld);

    return {
        enterWorld: (worldId: number) => {
            ws.send({
                action: 'enter.world',
                data: worldId
            });
        },
        leaveWorld: () => {
            ws.send({
                action: 'leave.world'
            });
        },
        getPlayer: async (token: string) => {
            const player = await getPlayer(token);
            if (player) {
                usePlayerStore.getState().setPlayer(player);
                return true;
            } else {
                return false;
            }
        }
    };
};
