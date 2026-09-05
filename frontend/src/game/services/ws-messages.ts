// RECEIVE MESSAGES
export interface WebSocketMessage {
    action: string;
    data: unknown;
};

export interface WebSocketFightMessage extends WebSocketMessage {
    action: "fight";
    data: {
        fightId: number;
        creatureName: string;
        creatureLevel: number;
    }
};

export interface WebSocketFightUpdate extends WebSocketMessage {
    action: "fight.update";
    data: {
        isPlayerAlive: boolean;
        isMonsterAlive: boolean;
        isFightOver: boolean;
        isPlayerAttacking: number;
        isCreatureAttacking: number;
        playerLife: number;
        playerStamina: number;
        creatureLife: number;
        creatureLevel: number;
    }
};

export interface WebSocketFightDropItems extends WebSocketMessage {
    action: "fight.drop.items";
    data: {
        id: number;
        itemName: string;
        itemPower: number;
        itemWeight: number;
        itemType: string;
        itemConsumableType: string | null;
    }[];
};

export interface WebSocketFightFinish extends WebSocketMessage {
    action: "fight.finish";
    data: {
        isPlayerAlive: boolean;
        isMonsterAlive: boolean;
        isFightOver: boolean;
        isPlayerAttacking: number;
        isCreatureAttacking: number;
        playerLife: number;
        playerStamina: number;
        creatureLife: number;
        creatureLevel: number;
    }
};

export type FightMessage = 
    | WebSocketFightMessage 
    | WebSocketFightUpdate 
    | WebSocketFightDropItems 
    | WebSocketFightFinish;

export interface WebSocketWorldEnterMessage extends WebSocketMessage {
    action: "world.enter";
    data: {
        id: number;
        worldName: string;
        worldMinLevel: number;
        worldMaxLevel: number;
    }
};

export type WorldMessage = WebSocketWorldEnterMessage;

export interface WebSocketInventoryUpdate extends WebSocketMessage {
    action: "inventory.update";
    data: {
        id: number;
        itemName: string;
        itemPower: number;
        itemWeight: number;
        itemType: string;
        itemConsumableType: string | null;
    }[]
};

export type InventoryMessage = WebSocketInventoryUpdate;

export type AnyMessage = FightMessage | WorldMessage | InventoryMessage;

// SEND MESSAGES
export interface WebSocketSendMessage {
    action: string;
    data?: unknown;
};

export interface WebSocketSendAttackMessage extends WebSocketSendMessage {
    action: "attack";
};

export interface WebSocketSendFleeMessage extends WebSocketSendMessage {
    action: "flee";
};

export type SendMessage = 
    | WebSocketSendAttackMessage 
    | WebSocketSendFleeMessage;
