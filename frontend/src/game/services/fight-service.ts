// WEBSOCKET
import type { WebSocketService } from '@/game/services/ws-service';

// WSocket MESSAGE
import type { 
    WebSocketFightMessage,
    WebSocketFightUpdate,
    WebSocketFightFinish,
    WebSocketFightDropItems,

    WebSocketSendAttackMessage,
    WebSocketSendFleeMessage
 } from '@/game/services/ws-messages';

// EVENTBUS
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

export interface FightService {
    attack: () => void;
    flee: () => void;
};

export function createFightService(ws: WebSocketService): FightService {
    const respFightActive = (message: WebSocketFightMessage) => {
        EventBus.emit(GAME_EVENTS.FIGHT, message.data);
    };
    const respFightUpdate = (message: WebSocketFightUpdate) => {
        EventBus.emit(GAME_EVENTS.FIGHT_UPDATE, message.data);
    };
    const respFightFinish = (message: WebSocketFightFinish) => {
        EventBus.emit(GAME_EVENTS.FIGHT_FINISH, message.data);
    };
    const respFightDropItems = (message: WebSocketFightDropItems) => {
        EventBus.emit(GAME_EVENTS.FIGHT_DROP_ITEMS, message.data);
    };

    ws.subscribe('fight', respFightActive);
    ws.subscribe('fight.update', respFightUpdate);
    ws.subscribe('fight.drop.items', respFightDropItems);
    ws.subscribe('fight.finish', respFightFinish);

    return {
        attack: () => {
            ws.send({
                action: 'attack'
            });
        },
        flee: () => {
            ws.send({
                action: 'flee'
            });
        }
    };
};
