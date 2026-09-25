// STORE
import { usePlayerStore } from '@/game/store/player-store';
import { usePlayerInventoryStore } from '@/game/store/player-inventory-store';

// WEBSOCKET
import type { WebSocketService } from "@/game/services/ws-service";

// WSocket MESSAGE
import type { 
    WebSocketInventoryUpdateMessage
 } from '@/game/services/ws-messages';

//INVENTORY ITEM
import { type PlayerInventoryItem } from '@/game/store/player-inventory-store';

// EVENT EMITTER
import { EventBus, GAME_EVENTS } from '@/game/event-bus';

export interface PlayerInventoryService {
    getInventory: () => void;
    useItem: (item: PlayerInventoryItem) => void;
    equipItem: (item: PlayerInventoryItem) => void;
    salvageItem: (item: PlayerInventoryItem) => void;
};

export function createPlayerInventoryService(ws: WebSocketService): PlayerInventoryService {
    const respInventoryUpdate = (message: WebSocketInventoryUpdateMessage) => {
        usePlayerInventoryStore.getState().setInventoryItems(message.data);
        
        EventBus.emit(GAME_EVENTS.UPDATE_PLAYER);
    };

    ws.subscribe('inventory.update', respInventoryUpdate);

    return {
        getInventory: () => {
            ws.send({
                action: 'get.inventory'
            });
        },
        useItem: (item: PlayerInventoryItem) => {
            ws.send({
                action: 'use.item',
                data: item.id
            });
        },
        equipItem: (item: PlayerInventoryItem) => {
            ws.send({
                action: 'use.item',
                data: item.id
            });
        },
        salvageItem: (item: PlayerInventoryItem) => {
            ws.send({
                action: 'salvage.item',
                data: item.id
            });
        },
    };
};
